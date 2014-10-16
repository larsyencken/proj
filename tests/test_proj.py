#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_proj
----------------------------------

Tests for `proj` module.
"""

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

import arrow
from click.testing import CliRunner

import proj


class TestProj(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp()
        self.archive = path.join(self.base, 'archive')
        self.current = path.join(self.base, 'current')
        proj.PROJ_ARCHIVE = self.archive
        os.mkdir(self.current)
        os.mkdir(self.archive)

        self.runner = CliRunner()

    def test_time_conversion(self):
        # we should be able to convert from a timestamp and back
        t = time.time()
        a = arrow.get(t)
        self.assertAlmostEqual(math.floor(t), a.timestamp)

    def test_latest_check_for_single_file(self):
        a = random_time()
        proj_name, proj_path = self.make_proj(a=a)
        assert path.isdir(proj_path)
        self.assertEqual(proj._last_modified(proj_path), a)

    def test_first_quarter_start(self):
        a = arrow.get(2000, 1, 1)
        self.assertEqual(proj._to_quarter(a),
                         ('2000', 'q1'))

    def test_first_quarter_end(self):
        a = arrow.get(2000, 3, 1)
        self.assertEqual(proj._to_quarter(a),
                         ('2000', 'q1'))

    def test_last_quarter_start(self):
        a = arrow.get(2000, 10, 1)
        self.assertEqual(proj._to_quarter(a),
                         ('2000', 'q4'))

    def test_last_quarter_end(self):
        a = arrow.get(2000, 12, 1)
        self.assertEqual(proj._to_quarter(a),
                         ('2000', 'q4'))

    def test_help(self):
        result = self.runner.invoke(proj.main)
        self.assertEqual(result.exit_code, 0)

    def test_list_empty(self):
        result = self.runner.invoke(proj.list)
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.output, '')

    def test_list_empty_with_glob(self):
        result = self.runner.invoke(proj.list, ['a', 'b', 'c'])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.output, '')

    def test_archive_project_in_current_dir_by_name(self):
        a = arrow.get(2000, 1, 1)
        proj_name, proj_path = self.make_proj(a=a)

        with chdir(self.current):
            result = self.runner.invoke(proj.archive, [proj_name])
            self.assertEqual(result.exit_code, 0)

        expected_loc = path.join(self.archive, '2000', 'q1', proj_name)
        assert path.isdir(expected_loc)
        assert path.exists(path.join(expected_loc, 'data'))

    def test_archive_project_by_full_path(self):
        a = arrow.get(2000, 1, 1)
        proj_name, proj_path = self.make_proj(a=a)

        result = self.runner.invoke(proj.archive, [proj_path])
        self.assertEqual(result.exit_code, 0)

        expected_loc = path.join(self.archive, '2000', 'q1', proj_name)
        assert path.isdir(expected_loc)
        assert path.exists(path.join(expected_loc, 'data'))

    def test_list_projects(self):
        # archive a project
        a = arrow.get(2000, 1, 1)
        proj_name, proj_path = self.make_proj(a=a)

        with chdir(self.current):
            result = self.runner.invoke(proj.archive, [proj_name])
            self.assertEqual(result.exit_code, 0)

        # list it
        expected = path.join('2000', 'q1', proj_name) + '\n'
        result2 = self.runner.invoke(proj.list)
        self.assertEqual(result2.exit_code, 0)
        self.assertEqual(result2.output, expected)

        # list it by suffix
        expected = path.join('2000', 'q1', proj_name) + '\n'
        result3 = self.runner.invoke(proj.list, [proj_name[:4]])
        self.assertEqual(result3.exit_code, 0)
        self.assertEqual(result3.output, expected)

    def test_archive_and_restore(self):
        # make a project
        proj_name, proj_path = self.make_proj()

        with chdir(self.current):
            # archive it
            result = self.runner.invoke(proj.archive, [proj_name])
            self.assertEqual(result.exit_code, 0)
            assert not path.isdir(proj_path)

            # restore it
            result2 = self.runner.invoke(proj.restore, [proj_name])
            self.assertEqual(result2.exit_code, 0)
            assert path.isdir(proj_path)

    def test_mkdir(self):
        dest = path.join(self.current, 'dog')
        assert not path.isdir(dest)
        proj._mkdir(dest)
        assert path.isdir(dest)

        dest2 = path.join(self.current, 'mouse', 'a', 'b', 'c')
        assert not path.isdir(dest2)
        proj._mkdir(dest2)
        assert path.isdir(dest2)

    def test_archive_dir_not_set(self):
        proj.PROJ_ARCHIVE = None
        result = self.runner.invoke(proj.main, ['list'])
        self.assertEqual(result.exit_code, 1)

    def test_archive_dir_doesnt_exist(self):
        proj.PROJ_ARCHIVE = '/tmp/does-not-exist'
        result = self.runner.invoke(proj.main, ['list'])
        self.assertEqual(result.exit_code, 1)

    def test_archive_nonexistent_folder(self):
        result = self.runner.invoke(proj.main, ['archive', 'old-buddy-fred'])
        self.assertEqual(result.exit_code, 1)

    def test_archive_empty_folder(self):
        proj_path = path.join(self.current, 'empty')
        os.mkdir(proj_path)
        result = self.runner.invoke(proj.main, ['archive', proj_path])
        self.assertEqual(result.exit_code, 1)

    def test_restore_missing_project(self):
        result = self.runner.invoke(proj.main, ['restore', 'my-dignity'])
        self.assertEqual(result.exit_code, 1)

    def test_restore_onto_existing_dir(self):
        # make a project
        proj_name, proj_path = self.make_proj()

        with chdir(self.current):
            # archive it
            result = self.runner.invoke(proj.archive, [proj_name])
            self.assertEqual(result.exit_code, 0)
            assert not path.isdir(proj_path)

            # put something else in the way
            os.mkdir(proj_name)

            result = self.runner.invoke(proj.main, ['restore', proj_name])
            self.assertEqual(result.exit_code, 1)

    def test_restore_the_most_recent_of_duplicates(self):
        name = random_string(8)

        with chdir(self.current):
            self.make_proj(name=name,
                           a=arrow.get(2020, 1, 1),
                           data='newer')
            self.runner.invoke(proj.archive, [name])

            self.make_proj(name=name,
                           a=arrow.get(2000, 1, 1),
                           data='older')
            self.runner.invoke(proj.archive, [name])

            self.runner.invoke(proj.restore, [name])
            with open(path.join(name, 'data')) as istream:
                data = istream.read()
            self.assertEqual(data, 'newer')

    def make_proj(self, name=None, a=None, data=''):
        a = a or random_time()
        t = a.timestamp

        proj_name = name or random_string(8)
        proj_path = path.join(self.current, proj_name)

        os.mkdir(proj_path)

        # make an empty file at proj/data
        f = path.join(proj_path, 'data')
        with open(f, 'w') as ostream:
            ostream.write(data)

        # set its modification time
        os.utime(f, (t, t))

        return proj_name, proj_path

    def tearDown(self):
        shutil.rmtree(self.base)


def random_time():
    return arrow.get(
        math.floor(random.random() * arrow.get(2038, 1, 1).timestamp)
    )


def random_string(l):
    return ''.join(random.choice(string.ascii_lowercase)
                   for i in range(l))


@contextlib.contextmanager
def chdir(d):
    current_dir = os.getcwd()
    try:
        os.chdir(d)
        yield
    finally:
        os.chdir(current_dir)


if __name__ == '__main__':
    unittest.main()
