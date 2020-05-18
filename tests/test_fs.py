# -*- coding: utf-8 -*-
#
#  test_fs.py
#  proj
#

import os
from os import path
import tempfile
import shutil

from proj import fs


class TestFs:
    def setup_method(self):
        self.old_cwd = os.getcwd()
        self.base = tempfile.mkdtemp()
        self.current = path.join(self.base, "current")
        fs.mkdir(self.current)
        os.chdir(self.current)

    def teardown_method(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.base)

    def test_mkdir(self):
        dest = path.join(self.current, "dog")
        assert not path.isdir(dest)
        fs.mkdir(dest)
        assert path.isdir(dest)

        dest2 = path.join(self.current, "mouse", "a", "b", "c")
        assert not path.isdir(dest2)
        fs.mkdir(dest2)
        assert path.isdir(dest2)

    def test_iter_single_file(self):
        filename = "example.out"
        fs.touch(filename)

        assert list(fs.iter_files(filename)) == [filename]
