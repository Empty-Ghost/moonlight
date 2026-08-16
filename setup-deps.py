#!/usr/bin/env python3
"""Install a pinned Moonlight dependency bundle without partial updates."""

from __future__ import annotations

import argparse
import hashlib
import os
import pathlib
import platform
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.request
import zipfile


ORGANIZATION = "moonlight-stream"
PREBUILT_REPO = "moonlight-qt-deps"
TAG = "v12"
MAX_ARCHIVE_MEMBERS = 100_000
MAX_EXTRACTED_BYTES = 2 * 1024 * 1024 * 1024

# Published release digests are copied here deliberately. Adding a new bundle
# is a reviewed app change, and v12 remains selectable for rollback.
BUNDLES = {
    "v12": {
        "mac": {
            "asset": "macOS-universal.zip",
            "size": 28_492_950,
            "sha256": "446228fb68d5aef4bb8791f08e5e98e38e6ecffdefac7633902fc463189a0f3c",
        },
        "steamlink": {
            "asset": "steamlink.zip",
            "size": 1_480_652,
            "sha256": "c4d58d8e8ffee46531cf9a93d9daf3fbc81f831685bba55c4222e995764025bf",
        },
    },
}


def get_platform_config(system: str | None = None) -> str:
    system = system or platform.system()
    if system == "Darwin":
        return "mac"
    if system == "Linux":
        return "steamlink"
    raise RuntimeError(f"Unsupported platform ({system})")


def hash_file(path: pathlib.Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            size += len(chunk)
            digest.update(chunk)
    return size, digest.hexdigest()


def verify_archive(path: pathlib.Path, bundle: dict[str, object]) -> None:
    size, digest = hash_file(path)
    if size != bundle["size"]:
        raise RuntimeError(f"Dependency archive size mismatch: expected {bundle['size']}, got {size}")
    if digest != bundle["sha256"]:
        raise RuntimeError("Dependency archive SHA-256 mismatch")


def safe_extract(archive: pathlib.Path, destination: pathlib.Path) -> None:
    with zipfile.ZipFile(archive) as source:
        members = source.infolist()
        if len(members) > MAX_ARCHIVE_MEMBERS:
            raise RuntimeError("Dependency archive contains too many entries")
        if sum(member.file_size for member in members) > MAX_EXTRACTED_BYTES:
            raise RuntimeError("Dependency archive expands beyond the safety limit")

        for member in members:
            name = member.filename
            path = pathlib.PurePosixPath(name)
            mode = member.external_attr >> 16
            if not name or "\\" in name or path.is_absolute() or ".." in path.parts:
                raise RuntimeError(f"Unsafe dependency archive path: {name!r}")
            if stat.S_ISLNK(mode):
                raise RuntimeError(f"Dependency archive contains a symlink: {name!r}")

            output = destination.joinpath(*path.parts)
            if member.is_dir():
                output.mkdir(parents=True, exist_ok=True)
                continue
            output.parent.mkdir(parents=True, exist_ok=True)
            with source.open(member) as compressed, output.open("xb") as extracted:
                shutil.copyfileobj(compressed, extracted)


def validate_contents(root: pathlib.Path, subfolder: str) -> None:
    for relative in ("include", "lib"):
        if not (root / relative).is_dir():
            raise RuntimeError(f"Dependency archive is missing required directory: {relative}")

    if subfolder != "mac":
        return

    required_libraries = ("libSDL2.dylib", "libavcodec.63.dylib", "libssl.3.dylib")
    for library in required_libraries:
        path = root / "lib" / library
        if not path.is_file():
            raise RuntimeError(f"Dependency archive is missing required library: lib/{library}")
        result = subprocess.run(
            ["/usr/bin/lipo", "-archs", str(path)], text=True, capture_output=True
        )
        architectures = set(result.stdout.split())
        if result.returncode or not {"arm64", "x86_64"}.issubset(architectures):
            raise RuntimeError(f"Dependency library is not universal arm64/x86_64: lib/{library}")


def atomic_install(staged: pathlib.Path, target: pathlib.Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    backup = staged.parent / "previous"
    had_target = target.exists()
    try:
        if had_target:
            os.replace(target, backup)
        os.replace(staged, target)
    except Exception:
        if had_target and backup.exists() and not target.exists():
            os.replace(backup, target)
        raise
    if backup.exists():
        shutil.rmtree(backup)


def install_bundle(
    *,
    tag: str,
    subfolder: str,
    repository_root: pathlib.Path,
    archive: pathlib.Path | None = None,
) -> None:
    try:
        bundle = BUNDLES[tag][subfolder]
    except KeyError as error:
        raise RuntimeError(f"No reviewed dependency digest for {tag}/{subfolder}") from error

    target = repository_root / "libs" / subfolder
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".moonlight-deps-", dir=target.parent) as temporary:
        temporary_path = pathlib.Path(temporary)
        downloaded = temporary_path / str(bundle["asset"])
        if archive is None:
            url = (
                f"https://github.com/{ORGANIZATION}/{PREBUILT_REPO}/releases/"
                f"download/{tag}/{bundle['asset']}"
            )
            print(f"Downloading {bundle['asset']} from immutable tag {tag}...")
            with urllib.request.urlopen(url) as response, downloaded.open("xb") as output:
                shutil.copyfileobj(response, output)
        else:
            shutil.copyfile(archive, downloaded)

        print("Verifying archive size and SHA-256...")
        verify_archive(downloaded, bundle)
        staged = temporary_path / "staged"
        staged.mkdir()
        print(f"Safely extracting {bundle['asset']}...")
        safe_extract(downloaded, staged)
        validate_contents(staged, subfolder)
        atomic_install(staged, target)
    print(f"Dependencies {tag} successfully deployed to {target}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tag",
        default=os.environ.get("MOONLIGHT_DEPS_TAG", TAG),
        help="reviewed dependency tag (MOONLIGHT_DEPS_TAG provides the rollback override)",
    )
    parser.add_argument("--archive", type=pathlib.Path, help="verify and install a local archive")
    args = parser.parse_args()
    try:
        install_bundle(
            tag=args.tag,
            subfolder=get_platform_config(),
            repository_root=pathlib.Path.cwd(),
            archive=args.archive,
        )
    except (OSError, RuntimeError, zipfile.BadZipFile) as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
