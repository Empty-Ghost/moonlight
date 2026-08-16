#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import importlib.util
import pathlib
import stat
import tempfile
import unittest
import zipfile
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("setup_deps", ROOT / "setup-deps.py")
assert SPEC and SPEC.loader
setup_deps = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(setup_deps)


def make_archive(path: pathlib.Path, entries: dict[str, bytes]) -> dict[str, object]:
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in entries.items():
            archive.writestr(name, content)
    data = path.read_bytes()
    return {"asset": path.name, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}


class SetupDepsTests(unittest.TestCase):
    def test_atomic_install_restores_previous_tree_on_swap_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            target = root / "libs" / "test"
            staged = root / "staging" / "new"
            target.mkdir(parents=True)
            staged.mkdir(parents=True)
            (target / "sentinel").write_text("old")
            (staged / "sentinel").write_text("new")
            real_replace = setup_deps.os.replace
            calls = 0

            def fail_new_install(source: pathlib.Path, destination: pathlib.Path) -> None:
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("injected swap failure")
                real_replace(source, destination)

            with mock.patch.object(setup_deps.os, "replace", side_effect=fail_new_install):
                with self.assertRaisesRegex(OSError, "injected"):
                    setup_deps.atomic_install(staged, target)
            self.assertEqual((target / "sentinel").read_text(), "old")

    def test_safe_extract_rejects_parent_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            archive = root / "bad.zip"
            make_archive(archive, {"../escaped": b"no"})
            with self.assertRaisesRegex(RuntimeError, "Unsafe"):
                setup_deps.safe_extract(archive, root / "output")
            self.assertFalse((root / "escaped").exists())

    def test_safe_extract_rejects_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            archive = root / "bad.zip"
            info = zipfile.ZipInfo("link")
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            with zipfile.ZipFile(archive, "w") as output:
                output.writestr(info, "../../outside")
            with self.assertRaisesRegex(RuntimeError, "symlink"):
                setup_deps.safe_extract(archive, root / "output")

    def test_digest_failure_preserves_existing_install(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            target = root / "libs" / "test"
            target.mkdir(parents=True)
            (target / "sentinel").write_text("old")
            archive = root / "bundle.zip"
            make_archive(archive, {"include/header": b"h", "lib/library": b"l"})
            setup_deps.BUNDLES["test"] = {"test": {
                "asset": archive.name,
                "size": archive.stat().st_size,
                "sha256": "0" * 64,
            }}
            with self.assertRaisesRegex(RuntimeError, "SHA-256"):
                setup_deps.install_bundle(
                    tag="test", subfolder="test", repository_root=root, archive=archive
                )
            self.assertEqual((target / "sentinel").read_text(), "old")

    def test_verified_archive_atomically_replaces_install(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            target = root / "libs" / "test"
            target.mkdir(parents=True)
            (target / "sentinel").write_text("old")
            archive = root / "bundle.zip"
            bundle = make_archive(archive, {"include/header": b"h", "lib/library": b"new"})
            setup_deps.BUNDLES["test"] = {"test": bundle}
            setup_deps.install_bundle(
                tag="test", subfolder="test", repository_root=root, archive=archive
            )
            self.assertFalse((target / "sentinel").exists())
            self.assertEqual((target / "lib" / "library").read_bytes(), b"new")


if __name__ == "__main__":
    unittest.main()
