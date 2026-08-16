#!/usr/bin/env python3
"""Generate a deterministic source-and-bundle SPDX inventory and notices file."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re


def spdx_id(value: str) -> str:
    return "SPDXRef-" + re.sub(r"[^A-Za-z0-9.-]", "-", value)


def license_expression(value: object) -> str:
    if not value:
        return "NOASSERTION"
    return str(value).split(" (", 1)[0]


def package_from_row(row: dict[str, object]) -> dict[str, object]:
    name = str(row["name"])
    commit = str(row["commit"])
    license_id = license_expression(row.get("license"))
    return {
        "SPDXID": spdx_id(name),
        "name": name,
        "versionInfo": commit,
        "downloadLocation": str(row.get("source_url") or "NOASSERTION"),
        "filesAnalyzed": False,
        "licenseConcluded": license_id,
        "licenseDeclared": license_id,
        "copyrightText": "NOASSERTION",
        "externalRefs": [
            {
                "referenceCategory": "PACKAGE-MANAGER",
                "referenceType": "purl",
                "referenceLocator": f"pkg:generic/{name}@{commit}",
            }
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=pathlib.Path, required=True)
    parser.add_argument("--spdx-output", type=pathlib.Path, required=True)
    parser.add_argument("--notices-output", type=pathlib.Path, required=True)
    args = parser.parse_args()

    inventory = json.loads(args.inventory.read_text())
    app = inventory["repositories"]["moonlight-qt"]
    rows = app["submodules"] + inventory["repositories"]["moonlight-qt-deps"]["submodules"]
    unique = {str(row["name"]): row for row in rows}
    packages = [package_from_row(unique[name]) for name in sorted(unique, key=str.casefold)]

    root_id = "SPDXRef-moonlight-qt"
    packages.insert(0, {
        "SPDXID": root_id,
        "name": "moonlight-qt",
        "versionInfo": app["commit"],
        "downloadLocation": app["remote"],
        "filesAnalyzed": False,
        "licenseConcluded": "GPL-3.0-or-later",
        "licenseDeclared": "GPL-3.0-or-later",
        "copyrightText": "NOASSERTION",
    })
    bundle = inventory["bundle"]
    integrity = bundle.get("integrity") or {}
    bundle_package = {
        "SPDXID": "SPDXRef-moonlight-qt-deps-bundle",
        "name": "moonlight-qt-deps-macos-bundle",
        "versionInfo": bundle["tag"],
        "downloadLocation": (
            "https://github.com/moonlight-stream/moonlight-qt-deps/releases/download/"
            f"{bundle['tag']}/{bundle['asset']}"
        ),
        "filesAnalyzed": False,
        "licenseConcluded": "NOASSERTION",
        "licenseDeclared": "NOASSERTION",
        "copyrightText": "NOASSERTION",
    }
    if integrity.get("sha256"):
        bundle_package["checksums"] = [{"algorithm": "SHA256", "checksumValue": integrity["sha256"]}]
    packages.append(bundle_package)

    relationships = [
        {"spdxElementId": root_id, "relationshipType": "DEPENDS_ON", "relatedSpdxElement": package["SPDXID"]}
        for package in packages[1:]
    ]
    generated = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    document = {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": f"moonlight-qt-{app['commit'][:12]}",
        "documentNamespace": f"https://moonlight-stream.org/spdx/moonlight-qt/{app['commit']}",
        "creationInfo": {"created": generated, "creators": ["Tool: docs/modernization/generate_sbom.py"]},
        "packages": packages,
        "relationships": relationships,
    }
    args.spdx_output.write_text(json.dumps(document, indent=2) + "\n")

    notices = ["# Third-party notices", "", "Generated from the pinned dependency inventory.", ""]
    for name in sorted(unique, key=str.casefold):
        row = unique[name]
        notices.extend([
            f"## {name}", "",
            f"- License: {row.get('license') or 'not yet identified'}",
            f"- Source: {row.get('source_url') or 'not yet identified'}",
            f"- Commit: `{row['commit']}`", "",
        ])
    args.notices_output.write_text("\n".join(notices))


if __name__ == "__main__":
    main()
