# -*- coding: utf-8 -*-
#
#  __init__.py
#  proj
#

from __future__ import print_function

__author__ = 'Lars Yencken'
__email__ = 'lars@yencken.org'
__version__ = '0.1.0'

import glob
import os
import shutil
import sys
from functools import reduce

import arrow
import click

PROJ_ARCHIVE = os.environ.get('PROJ_ARCHIVE')


def bail(message):
    click.echo(message, err=True)
    sys.exit(1)


@click.group()
def main():
    """
    proj is a tool for managing many different projects, and archiving
    projects that you're no longer actively working on.

    It assumes you have a working folder containing active projects,
    and an archive folder with inactive projects. proj helps organise
    inactive projects by year and by quarter (e.g. 2013/q3/my-project).

    proj needs an archive directory specified by the PROJ_ARCHIVE
    environment variable.
    """
    if PROJ_ARCHIVE is None:
        bail('please set PROJ_ARCHIVE to your archive\'s location')

    if not os.path.isdir(PROJ_ARCHIVE):
        bail('archive directory does not exist: ' + PROJ_ARCHIVE)


@click.command()
@click.argument('folder', nargs=-1)
@click.option('-n', '--dry-run',
              is_flag=True,
              help="Don't make any changes")
def archive(folder, dry_run=False):
    "Move an active project to the archive."
    # error handling on archive_dir already done in main()

    for f in folder:
        if not os.path.isdir(f):
            bail('folder does not exist: ' + f)

    _archive_safe(folder, PROJ_ARCHIVE, dry_run=dry_run)


def _last_modified(folder):
    try:
        return max(_time_modified(f) for f in _iter_files(folder))
    except ValueError:
        bail('no files in folder: ' + folder)


def _iter_files(folder):
    for dirname, subdirs, filenames in os.walk(folder):
        for basename in filenames:
            filename = os.path.join(dirname, basename)
            yield filename


def _time_modified(filename):
    return arrow.get(os.stat(filename).st_mtime)


def _to_quarter(t):
    return str(t.year), 'q' + str(1 + (t.month - 1) // 3)


def _archive_safe(folders, archive_dir, dry_run=False):
    for folder in folders:
        t = _last_modified(folder)
        year, quarter = _to_quarter(t)
        dest_dir = os.path.join(archive_dir, year, quarter,
                                os.path.basename(folder))

        print(folder, '-->', dest_dir)
        if not dry_run:
            parent_dir = os.path.dirname(dest_dir)
            _mkdir(parent_dir)
            shutil.move(folder, dest_dir)


def _mkdir(p):
    "The equivalent of 'mkdir -p' in shell."
    isdir = os.path.isdir

    stack = [os.path.abspath(p)]
    while not isdir(stack[-1]):
        parent_dir = os.path.dirname(stack[-1])
        stack.append(parent_dir)

    while stack:
        p = stack.pop()
        if not isdir(p):
            os.mkdir(p)


@click.command()
@click.argument('pattern', nargs=-1)
def list(pattern=()):
    "List the contents of the archive directory."
    # strategy: pick the intersection of all the patterns the user provides
    globs = ['*{0}*'.format(p) for p in pattern] + ['*']

    matches = []
    offset = len(PROJ_ARCHIVE) + 1
    for suffix in globs:
        glob_pattern = os.path.join(PROJ_ARCHIVE, '*', '*', suffix)
        matches.append(set(
            f[offset:] for f in glob.glob(glob_pattern)
        ))

    matches = reduce(lambda x, y: x.intersection(y),
                     matches)

    for m in sorted(matches):
        print(m)


@click.command()
@click.argument('folder')
def restore(folder):
    "Restore a project from the archive."
    if os.path.isdir(folder):
        bail('a folder of the same name already exists!')

    pattern = os.path.join(PROJ_ARCHIVE, '*', '*', folder)
    matches = glob.glob(pattern)
    if not matches:
        bail('no project matches: ' + folder)

    if len(matches) > 1:
        print('Warning: multiple matches, picking the most recent',
              file=sys.stderr)

    source = sorted(matches)[-1]
    print(source, '-->', folder)
    shutil.move(source, '.')


main.add_command(archive)
main.add_command(list)
main.add_command(restore)


if __name__ == '__main__':
    main()
