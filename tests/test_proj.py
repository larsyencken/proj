#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import path
import contextlib
import math
import os
import random
import shutil
import string
import tempfile
import time
import unittest
from unittest.mock import patch
from typing import Optional

import arrow
import pytest
from click.testing import CliRunner

import proj
from proj.configfile import Config
from proj import fs


class TestProj:
    def setup_method(self):
        self.base = tempfile.mkdtemp()

        self.archive = path.join(self.base, "archive")
        fs.mkdir(self.archive)

        self.current = path.join(self.base, "current")
        fs.mkdir(self.current)

        self.old_cwd = os.getcwd()
        os.chdir(self.current)

        self.runner = CliRunner()
        self.no_compression = Config(
            archive_dir=self.archive, compression=False, compression_format=None
        )
        self.bz2_compression = Config(
            archive_dir=self.archive, compression=True, compression_format="bztar"
        )

    def teardown_method(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.base)

    def test_time_conversion(self):
        # we should be able to convert from a timestamp and back
        t = time.time()
        a = arrow.get(t)
        assert math.floor(t) == pytest.approx(a.timestamp)

    def test_latest_check_for_single_file(self):
        a = random_time()
        proj_name, proj_path = self.make_proj(a=a)
        assert path.isdir(proj_path)
        assert fs.last_modified(proj_path) == a

    def test_help(self):
        result = self.runner.invoke(proj.main)
        assert result.exit_code == 0

    @patch("proj.configfile.Config.autoload")
    def test_list_empty(self, autoload):
        autoload.return_value = self.no_compression

        result = self.runner.invoke(proj.list)
        assert result.exit_code == 0
        assert result.output == ""

    @patch("proj.configfile.Config.autoload")
    def test_list_empty_with_glob(self, autoload):
        autoload.return_value = self.no_compression

        result = self.runner.invoke(proj.list, ["a", "b", "c"])
        assert result.exit_code == 0
        assert result.output == ""

    @patch("proj.configfile.Config.autoload")
    def test_archive_project_in_current_dir_by_name_uncompressed(self, autoload):
        autoload.return_value = self.no_compression

        a = arrow.get(2000, 1, 1)
        proj_name, proj_path = self.make_proj(a=a)

        result = self.runner.invoke(proj.archive, [proj_name])
        assert result.exit_code == 0

        expected_loc = path.join(self.archive, "2000", "q1", proj_name)
        assert path.isdir(expected_loc)
        assert path.exists(path.join(expected_loc, "data"))

    @patch("proj.configfile.Config.autoload")
    def test_archive_project_in_current_dir_by_name_compressed(self, autoload):
        autoload.return_value = self.bz2_compression

        a = arrow.get(2000, 1, 1)
        proj_name, proj_path = self.make_proj(a=a)

        result = self.runner.invoke(proj.archive, [proj_name])
        assert result.exit_code == 0

        expected_loc = path.join(self.archive, "2000", "q1", proj_name + ".tar.bz2")
        assert path.exists(expected_loc)

    @patch("proj.configfile.Config.autoload")
    def test_archive_project_by_full_path_compressed(self, autoload):
        autoload.return_value = self.bz2_compression

        a = arrow.get(2000, 1, 1)
        proj_name, proj_path = self.make_proj(a=a)

        result = self.runner.invoke(proj.archive, [proj_path])
        assert result.exit_code == 0

        expected_loc = path.join(self.archive, "2000", "q1", f"{proj_name}.tar.bz2")
        assert path.exists(expected_loc)

    @patch("proj.configfile.Config.autoload")
    def test_archive_project_by_full_path_uncompressed(self, autoload):
        autoload.return_value = self.no_compression

        a = arrow.get(2000, 1, 1)
        proj_name, proj_path = self.make_proj(a=a)

        result = self.runner.invoke(proj.archive, [proj_path])
        assert result.exit_code == 0

        expected_loc = path.join(self.archive, "2000", "q1", proj_name)
        assert path.isdir(expected_loc)
        assert path.exists(path.join(expected_loc, "data"))

    @patch("proj.configfile.Config.autoload")
    def test_list_projects(self, autoload):
        autoload.return_value = self.no_compression

        # archive a project
        a = arrow.get(2000, 1, 1)
        proj_name, proj_path = self.make_proj(a=a)

        result = self.runner.invoke(proj.archive, [proj_name])
        assert result.exit_code == 0

        # list it
        expected = path.join("2000", "q1", proj_name) + "\n"
        result2 = self.runner.invoke(proj.list)
        assert result2.exit_code == 0
        assert result2.output == expected

        # list it by suffix
        expected = path.join("2000", "q1", proj_name) + "\n"
        result3 = self.runner.invoke(proj.list, [proj_name[:4]])
        assert result3.exit_code == 0
        assert result3.output == expected

    @patch("proj.configfile.Config.autoload")
    def test_archive_and_restore(self, autoload):
        autoload.return_value = self.no_compression

        # make a project
        proj_name, proj_path = self.make_proj()

        # archive it
        result = self.runner.invoke(proj.archive, [proj_name])
        assert result.exit_code == 0
        assert not path.isdir(proj_path)

        # restore it
        result2 = self.runner.invoke(proj.restore, [proj_name])
        assert result2.exit_code == 0
        assert path.isdir(proj_path)

    @patch("proj.configfile.Config._get_config_file")
    def test_no_config(self, get_config_file):
        get_config_file.return_value = "does-not-exist.yml"

        result = self.runner.invoke(proj.main, ["list"])
        assert result.exit_code == 1

    def test_archive_nonexistent_folder(self):
        result = self.runner.invoke(proj.main, ["archive", "old-buddy-fred"])
        assert result.exit_code == 1

    def test_archive_empty_folder(self):
        proj_path = path.join(self.current, "empty")
        os.mkdir(proj_path)
        result = self.runner.invoke(proj.main, ["archive", proj_path])
        assert result.exit_code == 1

    def test_restore_missing_project(self):
        result = self.runner.invoke(proj.main, ["restore", "my-dignity"])
        assert result.exit_code == 1

    @patch("proj.configfile.Config.autoload")
    def test_restore_onto_existing_dir(self, autoload):
        autoload.return_value = self.no_compression

        # make a project
        proj_name, proj_path = self.make_proj()

        # archive it
        result = self.runner.invoke(proj.archive, [proj_name])
        assert result.exit_code == 0
        assert not path.isdir(proj_path)

        # put something else in the way
        os.mkdir(proj_name)

        result = self.runner.invoke(proj.main, ["restore", proj_name])
        assert result.exit_code == 1

    @patch("proj.configfile.Config.autoload")
    def test_restore_the_most_recent_of_duplicates(self, autoload):
        autoload.return_value = self.no_compression

        name = random_string(8)

        self.make_proj(name=name, a=arrow.get(2020, 1, 1), data="newer")
        self.runner.invoke(proj.archive, [name])

        self.make_proj(name=name, a=arrow.get(2000, 1, 1), data="older")
        self.runner.invoke(proj.archive, [name])

        self.runner.invoke(proj.restore, [name])
        with open(path.join(name, "data")) as istream:
            data = istream.read()
        assert data == "newer"

    def make_proj(
        self,
        name: Optional[str] = None,
        a: Optional[arrow.Arrow] = None,
        data: str = "",
    ):
        a = a or random_time()
        t = a.timestamp

        proj_name = name or random_string(8)
        proj_path = path.join(self.current, proj_name)

        os.mkdir(proj_path)

        # make an empty file at proj/data
        f = path.join(proj_path, "data")
        with open(f, "w") as ostream:
            ostream.write(data)

        # set its modification time
        os.utime(f, (t, t))

        return proj_name, proj_path


def random_time():
    return arrow.get(math.floor(random.random() * arrow.get(2038, 1, 1).timestamp))


def random_string(length):
    return "".join(random.choice(string.ascii_lowercase) for i in range(length))


@contextlib.contextmanager
def chdir(d):
    current_dir = os.getcwd()
    try:
        os.chdir(d)
        yield
    finally:
        os.chdir(current_dir)


if __name__ == "__main__":
    unittest.main()
