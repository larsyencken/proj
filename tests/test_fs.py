# -*- coding: utf-8 -*-
#
#  test_fs.py
#  proj
#

from os import path
import tempfile

from proj import fs


class TestFs:
    def setup_class(cls):
        cls.base = tempfile.mkdtemp()
        cls.current = path.join(cls.base, "current")

    def test_mkdir(self):
        dest = path.join(self.current, "dog")
        assert not path.isdir(dest)
        fs.mkdir(dest)
        assert path.isdir(dest)

        dest2 = path.join(self.current, "mouse", "a", "b", "c")
        assert not path.isdir(dest2)
        fs.mkdir(dest2)
        assert path.isdir(dest2)
