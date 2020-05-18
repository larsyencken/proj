# -*- coding: utf-8 -*-
#
#  test_logic.py
#  proj
#

import os
from os import path
import tempfile
import shutil
import time
import math
from typing import Optional
import random
import string
from unittest.mock import patch

import arrow
import pytest

from proj import logic, fs, configfile


def test_first_quarter_start():
    a = arrow.get(2000, 1, 1)
    assert logic._to_quarter(a) == ("2000", "q1")


def test_first_quarter_end():
    a = arrow.get(2000, 3, 1)
    assert logic._to_quarter(a) == ("2000", "q1")


def test_last_quarter_start():
    a = arrow.get(2000, 10, 1)
    assert logic._to_quarter(a) == ("2000", "q4")


def test_last_quarter_end():
    a = arrow.get(2000, 12, 1)
    assert logic._to_quarter(a) == ("2000", "q4")


class TestMainLogic:
    def setup_method(self):
        self.base = tempfile.mkdtemp()

        self.archive = path.join(self.base, "archive")
        fs.mkdir(self.archive)

        self.current = path.join(self.base, "current")
        fs.mkdir(self.current)

        self.old_cwd = os.getcwd()
        os.chdir(self.current)

        self.no_compression = configfile.Config(
            archive_dir=self.archive, compression=False, compression_format=None
        )
        self.bz2_compression = configfile.Config(
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

    def test_list_empty(self):
        projects = logic.list_projects([], self.no_compression)
        assert projects == []

    def test_list_empty_with_glob(self):
        projects = logic.list_projects(["a", "b", "c"], self.no_compression)
        assert projects == []

    def test_archive_project_in_current_dir_by_name_uncompressed(self):
        a = arrow.get(2000, 1, 1)
        proj_name, proj_path = self.make_proj(a=a)

        logic.archive(proj_name, self.no_compression)

        expected_loc = path.join(self.archive, "2000", "q1", proj_name)
        assert path.isdir(expected_loc)
        assert path.exists(path.join(expected_loc, "data"))

    def test_archive_project_in_current_dir_by_name_compressed(self):
        a = arrow.get(2000, 1, 1)
        proj_name, proj_path = self.make_proj(a=a)

        logic.archive(proj_name, self.bz2_compression)

        expected_loc = path.join(self.archive, "2000", "q1", proj_name + ".tar.bz2")
        assert path.exists(expected_loc)

    def test_archive_project_by_full_path_compressed(self):
        a = arrow.get(2000, 1, 1)
        proj_name, proj_path = self.make_proj(a=a)

        logic.archive(proj_path, self.bz2_compression)

        expected_loc = path.join(self.archive, "2000", "q1", f"{proj_name}.tar.bz2")
        assert path.exists(expected_loc)

    def test_archive_project_by_full_path_uncompressed(self):
        a = arrow.get(2000, 1, 1)
        proj_name, proj_path = self.make_proj(a=a)

        logic.archive(proj_path, self.no_compression)

        expected_loc = path.join(self.archive, "2000", "q1", proj_name)
        assert path.isdir(expected_loc)
        assert path.exists(path.join(expected_loc, "data"))

    def test_list_projects(self):
        # archive a project
        a = arrow.get(2000, 1, 1)
        proj_name, proj_path = self.make_proj(a=a)

        logic.archive(proj_name, self.no_compression)

        expected = [path.join("2000", "q1", proj_name)]

        # list it
        projects = logic.list_projects([], self.no_compression)
        assert projects == expected

        # list it by prefix
        prefix = proj_name[:4]
        projects = logic.list_projects([prefix], self.no_compression)
        assert projects == expected

    def test_archive_and_restore(self):
        # make a project
        proj_name, proj_path = self.make_proj()

        # archive it
        logic.archive(proj_name, self.no_compression)
        assert not path.isdir(proj_path)

        # restore it
        logic.restore(proj_name, self.no_compression)
        assert path.isdir(proj_path)

    def test_archive_dir_doesnt_exist(self):
        config = configfile.Config(archive_dir="/tmp/does-not-exist")
        logic.list_projects([], config)

    def test_archive_nonexistent_folder(self):
        with pytest.raises(logic.CommandError):
            logic.archive("old-buddy-fred", self.no_compression)

    def test_archive_empty_folder(self):
        proj_path = path.join(self.current, "empty")
        os.mkdir(proj_path)
        with pytest.raises(logic.CommandError):
            logic.archive(proj_path, self.no_compression)

    def test_restore_missing_project(self):
        with pytest.raises(logic.CommandError):
            logic.restore("my-dignity", self.no_compression)

    def test_restore_compressed(self):
        data = "alakazam"
        proj_name, _ = self.make_proj(data=data)

        logic.archive(proj_name, self.bz2_compression)
        logic.restore(proj_name, self.bz2_compression)

        with open(f"{proj_name}/data") as istream:
            assert istream.read().strip() == data

    def test_restore_onto_existing_dir(self):
        # make a project
        proj_name, proj_path = self.make_proj()

        # archive it
        logic.archive(proj_name, self.no_compression)
        assert not path.isdir(proj_path)

        # put something else in the way
        os.mkdir(proj_name)

        with pytest.raises(logic.CommandError):
            logic.restore(proj_name, self.no_compression)

    def test_restore_the_most_recent_of_duplicates(self):
        name = random_string(8)

        self.make_proj(name=name, a=arrow.get(2020, 1, 1), data="newer")
        logic.archive(name, self.no_compression)

        self.make_proj(name=name, a=arrow.get(2000, 1, 1), data="older")
        logic.archive(name, self.no_compression)

        logic.restore(name, self.no_compression)
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

    @patch("shutil.make_archive")
    def test_archive_compressed_failure(self, make_archive):

        src_path, _ = self.make_proj()
        dest_path = logic._archive_path(src_path, self.bz2_compression)

        archive_file = f"{dest_path}.tar.bz2"

        # imagine we fail part way through writing the archive
        def touch_and_fail(*args, **kwargs):
            fs.mkdir(os.path.dirname(archive_file))
            fs.touch(archive_file)
            raise KeyError()

        make_archive.side_effect = touch_and_fail

        # check that we re-raise the exception
        with pytest.raises(KeyError):
            # actuall call we're testing
            logic._archive_compressed(
                src_path,
                dest_path,
                compression_format="bztar",
                compression_ext=".tar.bz2",
            )

        # check that we deleted it
        assert not os.path.exists(archive_file)


def random_time():
    return arrow.get(math.floor(random.random() * arrow.get(2038, 1, 1).timestamp))


def random_string(length):
    return "".join(random.choice(string.ascii_lowercase) for i in range(length))
