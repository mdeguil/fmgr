import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from atelier1_fmgr import FileManager, FileSelection, FileSystem, Output


class FakeSelection(FileSelection):
    def __init__(self, files=None):
        self.files = list(files or [])
        self.cleared = False

    def get_selected_files(self):
        return self.files

    def clear_selection(self):
        self.cleared = True
        self.files = []


class FakeFileSystem(FileSystem):
    """In-memory file system; `files` and `dirs` are sets of paths."""

    def __init__(self, files=(), dirs=(), fail_with=None):
        self.files = set(files)
        self.dirs = set(dirs)
        self.fail_with = fail_with
        self.calls = []

    def _maybe_fail(self):
        if self.fail_with:
            raise self.fail_with

    def exists(self, path):
        return path in self.files or path in self.dirs

    def is_file(self, path):
        return path in self.files

    def is_dir(self, path):
        return path in self.dirs

    def copy(self, source, destination):
        self._maybe_fail()
        self.calls.append(("copy", source, destination))

    def move(self, source, destination):
        self._maybe_fail()
        self.calls.append(("move", source, destination))

    def remove_file(self, path):
        self._maybe_fail()
        self.calls.append(("remove_file", path))

    def remove_tree(self, path):
        self._maybe_fail()
        self.calls.append(("remove_tree", path))


class FakeOutput(Output):
    def __init__(self):
        self.messages = []

    def show(self, message):
        self.messages.append(message)


class FileManagerTestCase(unittest.TestCase):
    def build(self, selected, files=(), dirs=(), fail_with=None):
        self.selection = FakeSelection(selected)
        self.fs = FakeFileSystem(files, dirs, fail_with)
        self.out = FakeOutput()
        return FileManager(self.selection, self.fs, self.out)


class TestCopy(FileManagerTestCase):
    def test_copies_each_existing_file(self):
        manager = self.build(["a", "b"], files={"a", "b"})
        manager.copy_files("dest")
        self.assertEqual(self.fs.calls, [("copy", "a", "dest"), ("copy", "b", "dest")])
        self.assertEqual(self.out.messages, ["2 file(s) copied"])
        self.assertTrue(self.selection.cleared)

    def test_skips_missing_file(self):
        manager = self.build(["a", "ghost"], files={"a"})
        manager.copy_files("dest")
        self.assertEqual(self.fs.calls, [("copy", "a", "dest")])

    def test_empty_selection(self):
        manager = self.build([])
        manager.copy_files("dest")
        self.assertEqual(self.fs.calls, [])
        self.assertEqual(self.out.messages, ["0 file(s) copied"])

    def test_error_is_reported_and_selection_kept(self):
        manager = self.build(["a"], files={"a"}, fail_with=OSError("boom"))
        manager.copy_files("dest")
        self.assertEqual(self.out.messages, ["Copy error: boom"])
        self.assertFalse(self.selection.cleared)


class TestMove(FileManagerTestCase):
    def test_moves_each_existing_file(self):
        manager = self.build(["a", "b"], files={"a"}, dirs={"b"})
        manager.move_files("dest")
        self.assertEqual(self.fs.calls, [("move", "a", "dest"), ("move", "b", "dest")])
        self.assertEqual(self.out.messages, ["2 file(s) moved"])
        self.assertTrue(self.selection.cleared)

    def test_skips_missing_file(self):
        manager = self.build(["ghost"])
        manager.move_files("dest")
        self.assertEqual(self.fs.calls, [])

    def test_error_is_reported_and_selection_kept(self):
        manager = self.build(["a"], files={"a"}, fail_with=OSError("boom"))
        manager.move_files("dest")
        self.assertEqual(self.out.messages, ["Move error: boom"])
        self.assertFalse(self.selection.cleared)


class TestDelete(FileManagerTestCase):
    def test_deletes_files_and_directories(self):
        manager = self.build(["f", "d"], files={"f"}, dirs={"d"})
        manager.delete_files()
        self.assertEqual(self.fs.calls, [("remove_file", "f"), ("remove_tree", "d")])
        self.assertEqual(self.out.messages, ["2 file(s)/folder(s) deleted"])
        self.assertTrue(self.selection.cleared)

    def test_ignores_missing_path(self):
        manager = self.build(["ghost"])
        manager.delete_files()
        self.assertEqual(self.fs.calls, [])

    def test_error_is_reported_and_selection_kept(self):
        manager = self.build(["f"], files={"f"}, fail_with=OSError("boom"))
        manager.delete_files()
        self.assertEqual(self.out.messages, ["Delete error: boom"])
        self.assertFalse(self.selection.cleared)


if __name__ == "__main__":
    unittest.main()
