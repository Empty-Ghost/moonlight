#!/usr/bin/env python3
"""Generate the Phase 0 dependency inventory from moonlight-qt and -qt-deps."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import re
import subprocess
from typing import Any


LICENSES = {
    "FFmpeg": "LGPL-2.1-or-later (GPL features disabled by bundle build)",
    "openssl": "Apache-2.0",
    "SDL": "Zlib",
    "sdl2-compat": "Zlib",
    "SDL_ttf": "Zlib",
    "dav1d": "BSD-2-Clause",
    "libplacebo": "LGPL-2.1-or-later",
    "Vulkan-Headers": "Apache-2.0",
    "opus": "BSD-3-Clause",
    "discord-rpc": "MIT",
    "Detours": "MIT",
    "Ne10": "Apache-2.0",
    "moonlight-common-c": "GPL-3.0-or-later",
    "enet": "MIT",
    "nanors": "BSD-2-Clause",
    "qmdnsengine": "LGPL-2.1-or-later",
    "SDL_GameControllerDB": "Zlib",
}


def run(cwd: pathlib.Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if check and result.returncode:
        raise RuntimeError(f"{' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def gitmodules(repo: pathlib.Path) -> dict[str, dict[str, str]]:
    path = repo / ".gitmodules"
    if not path.exists():
        return {}
    output: dict[str, dict[str, str]] = {}
    section = ""
    for line in path.read_text().splitlines():
        match = re.match(r'\[submodule "(.+)"\]', line.strip())
        if match:
            section = match.group(1)
            output[section] = {}
        elif "=" in line and section:
            key, value = (piece.strip() for piece in line.split("=", 1))
            output[section][key] = value
    return output


def submodules(repo: pathlib.Path) -> list[dict[str, Any]]:
    modules = gitmodules(repo)
    rows: list[dict[str, Any]] = []
    for name, values in sorted(modules.items()):
        path = values["path"]
        sha = run(repo, "git", "rev-parse", f"HEAD:{path}")
        checked_out = (repo / path / ".git").exists()
        describe = None
        if checked_out:
            describe = run(repo / path, "git", "describe", "--tags", "--always", check=False) or None
        rows.append({
            "name": name,
            "path": path,
            "source_url": values.get("url"),
            "branch_hint": values.get("branch"),
            "commit": sha,
            "describe": describe,
            "license": LICENSES.get(name) or LICENSES.get(pathlib.Path(path).name),
        })
    return rows


def nested_app_dependencies(app_repo: pathlib.Path) -> list[dict[str, Any]]:
    common = app_repo / "moonlight-common-c" / "moonlight-common-c"
    rows = []
    for name in ("enet", "nanors"):
        sha = run(common, "git", "rev-parse", f"HEAD:{name}")
        url = gitmodules(common).get(name, {}).get("url")
        rows.append({"name": name, "path": f"moonlight-common-c/{name}",
                     "source_url": url, "commit": sha, "license": LICENSES[name]})
    return rows


def actions(repo: pathlib.Path) -> list[dict[str, str]]:
    rows = []
    for path in sorted((repo / ".github" / "workflows").glob("*.yml")):
        for number, line in enumerate(path.read_text().splitlines(), 1):
            match = re.search(r"\buses:\s*([^\s#]+)", line)
            if match:
                value = match.group(1)
                rows.append({"workflow": str(path.relative_to(repo)), "line": str(number),
                             "action": value, "immutable": bool(re.search(r"@[0-9a-f]{40}$", value))})
    return rows


def dylibs(app_repo: pathlib.Path) -> list[dict[str, Any]]:
    rows = []
    for path in sorted((app_repo / "libs" / "mac" / "lib").glob("*.dylib")):
        archs = run(app_repo, "lipo", "-archs", str(path), check=False).split()
        identity = run(app_repo, "otool", "-D", str(path), check=False).splitlines()
        rows.append({"file": path.name, "architectures": archs,
                     "install_name": identity[-1].strip() if len(identity) > 1 else None})
    return rows


def packaged_machos(bundle: pathlib.Path) -> list[dict[str, Any]]:
    rows = []
    for item in sorted(path for path in bundle.rglob("*") if path.is_file() and not path.is_symlink()):
        kind = subprocess.run(["/usr/bin/file", "-b", str(item)], text=True,
                              capture_output=True).stdout
        if "Mach-O" not in kind:
            continue
        archs = subprocess.run(["lipo", "-archs", str(item)], text=True,
                               capture_output=True).stdout.split()
        linked = subprocess.run(["otool", "-L", str(item)], text=True,
                                capture_output=True).stdout.splitlines()[1:]
        rows.append({"path": str(item.relative_to(bundle)), "architectures": archs,
                     "linked_libraries": [line.strip() for line in linked]})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--app-repo", type=pathlib.Path, default=pathlib.Path.cwd())
    parser.add_argument("--deps-repo", type=pathlib.Path, required=True)
    parser.add_argument("--bundle-archive", type=pathlib.Path,
                        help="Downloaded macOS bundle used to record size and SHA-256")
    parser.add_argument("--app-bundle", type=pathlib.Path,
                        help="Deployed Moonlight.app used to inventory the transitive Mach-O closure")
    parser.add_argument("--output", type=pathlib.Path,
                        default=pathlib.Path("docs/modernization/dependencies.json"))
    args = parser.parse_args()
    app = args.app_repo.resolve()
    deps = args.deps_repo.resolve()
    setup = (app / "setup-deps.py").read_text()
    bundle_tag = re.search(r'^TAG\s*=\s*"([^"]+)"', setup, re.MULTILINE).group(1)
    workflow_text = (deps / ".github/workflows/build-win-mac.yml").read_text()
    vulkan = re.search(r"version:\s*([0-9.]+)", workflow_text).group(1)
    macos_min = re.search(r"macos_min:\s*'([^']+)'", workflow_text).group(1)
    qt_version = re.search(r"qt_version:\s*([0-9.]+)",
                           (app / ".github/workflows/build-win-mac.yml").read_text()).group(1)

    bundle_integrity = None
    if args.bundle_archive:
        archive = args.bundle_archive.resolve()
        digest = hashlib.sha256()
        with archive.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        bundle_integrity = {"size_bytes": archive.stat().st_size, "sha256": digest.hexdigest()}

    inventory = {
        "schema_version": 1,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "repositories": {
            "moonlight-qt": {"commit": run(app, "git", "rev-parse", "HEAD"),
                              "remote": run(app, "git", "remote", "get-url", "upstream"),
                              "submodules": submodules(app) + nested_app_dependencies(app)},
            "moonlight-qt-deps": {"commit": run(deps, "git", "rev-parse", "HEAD"),
                                   "tag": run(deps, "git", "describe", "--tags", "--exact-match"),
                                   "remote": run(deps, "git", "remote", "get-url", "origin"),
                                   "submodules": submodules(deps)},
        },
        "bundle": {"tag": bundle_tag, "asset": "macOS-universal.zip", "integrity": bundle_integrity,
                   "deployment_target_declared": macos_min, "dylibs": dylibs(app),
                   "packaged_machos": packaged_machos(args.app_bundle.resolve()) if args.app_bundle else []},
        "toolchain_pins": {"qt": qt_version, "vulkan_sdk_moltenvk": vulkan,
                           "create_dmg": "unpinned npm package", "aqtinstall": "073e34d7c2ab4ae6961ed7cca690b3abd5ba5a7e"},
        "ci_actions": {"moonlight-qt": actions(app), "moonlight-qt-deps": actions(deps)},
        "system_frameworks": ["VideoToolbox", "AVFoundation", "CoreVideo", "CoreGraphics",
                              "CoreMedia", "AppKit", "Metal", "QuartzCore"],
        "repository_resources": ["ModeSeven.ttf", "icons", "Metal/HLSL/GLSL shaders",
                                 "translations", "SDL GameControllerDB"],
        "notes": [
            "Build options and patches are authoritative in the pinned moonlight-qt-deps scripts and patches directory.",
            "Transitive dylib closure is recorded from the downloaded v12 macOS artifact; deeper SBOM work belongs to Phase 2.",
            "Candidate versions, CVEs, and update decisions are intentionally deferred to Phase 2.",
        ],
    }
    output = args.output if args.output.is_absolute() else app / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(inventory, indent=2) + "\n")


if __name__ == "__main__":
    main()
