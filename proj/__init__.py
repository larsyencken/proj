# -*- coding: utf-8 -*-
#
#  __init__.py
#  proj
#

from __future__ import print_function

__author__ = "Lars Yencken"
__email__ = "lars@yencken.org"
__version__ = "0.2.0"

import glob
import os
import shutil
import sys
from functools import reduce
import datetime as dt
from typing import NoReturn, Tuple, List, Iterator

import arrow
import click

PROJ_ARCHIVE = os.environ.get("PROJ_ARCHIVE")

COMPRESS_FORMAT = "bztar"
COMPRESS_EXT = ".tar.bz2"


def bail(message: str) -> NoReturn:
    click.echo(message, err=True)
    sys.exit(1)


def get_archive_dir() -> str:
    if PROJ_ARCHIVE is None:
        bail("please set PROJ_ARCHIVE to your archive's location")

    if not os.path.isdir(PROJ_ARCHIVE):
        bail("archive directory does not exist: " + PROJ_ARCHIVE)

    return PROJ_ARCHIVE


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
    pass


@click.command()
@click.argument("folder", nargs=-1)
@click.option("-n", "--dry-run", is_flag=True, help="Don't make any changes")
@click.option("--no-compress", is_flag=True, help="Do not compress the folder")
def archive(folder: List[str], dry_run: bool = False, no_compress: bool = False):
    "Move an active project to the archive."
    # error handling on archive_dir already done in main()

    for f in folder:
        if not os.path.exists(f):
            bail("folder does not exist: " + f)

    archive_dir = get_archive_dir()
    _archive_safe(folder, archive_dir, dry_run=dry_run, compress=not no_compress)


def _last_modified(folder: str) -> dt.datetime:
    try:
        return max(
            _time_modified(f) for f in _iter_files(folder) if not os.path.islink(f)
        )

    except ValueError:
        bail("no files in folder: " + folder)


def _iter_files(folder: str) -> Iterator[str]:
    if os.path.isdir(folder):
        for dirname, subdirs, filenames in os.walk(folder):
            for basename in filenames:
                filename = os.path.join(dirname, basename)
                yield filename
    else:
        # it's actually just a file
        yield folder


def _time_modified(filename: str) -> arrow.Arrow:
    return arrow.get(os.stat(filename).st_mtime)


def _to_quarter(t: dt.datetime) -> Tuple[str, str]:
    return str(t.year), "q" + str(1 + (t.month - 1) // 3)


def _archive_safe(
    folders: List[str], archive_dir: str, dry_run: bool = False, compress: bool = False
) -> None:
    for folder in folders:
        t = _last_modified(folder)
        year, quarter = _to_quarter(t)
        dest_dir = os.path.join(archive_dir, year, quarter, os.path.basename(folder))

        print(folder, "-->", dest_dir)
        if not dry_run:
            if compress and os.path.isdir(folder):
                _compress_and_archive(folder, dest_dir)
            else:
                _archive_folder(folder, dest_dir)


def _archive_folder(folder, dest_dir):
    parent_dir = os.path.dirname(dest_dir)
    _mkdir(parent_dir)
    shutil.move(folder, dest_dir)


def _compress_and_archive(src_folder, dst_folder):
    parent_dir = os.path.dirname(dst_folder)
    _mkdir(parent_dir)

    try:
        shutil.make_archive(dst_folder, COMPRESS_FORMAT, src_folder)
    except Exception as e:
        os.unlink(dst_folder + COMPRESS_EXT)
        raise e

    shutil.rmtree(src_folder)


def _mkdir(p: str) -> None:
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
@click.argument("pattern", nargs=-1)
def list(pattern: List[str]) -> None:
    "List the contents of the archive directory."
    # strategy: pick the intersection of all the patterns the user provides
    globs = ["*{0}*".format(p) for p in pattern] + ["*"]
    archive_dir = get_archive_dir()

    match_sets = []
    offset = len(archive_dir) + 1
    for suffix in globs:
        glob_pattern = os.path.join(archive_dir, "*", "*", suffix)
        match_set = set(f[offset:] for f in glob.glob(glob_pattern))
        match_sets.append(match_set)

    final_set = reduce(lambda x, y: x.intersection(y), match_sets)

    for m in sorted(final_set):
        print(m)


@click.command()
@click.argument("folder")
def restore(folder: str) -> None:
    "Restore a project from the archive."
    if os.path.isdir(folder):
        bail("a folder of the same name already exists!")

    source = _find_restore_match(folder)

    if source.endswith(COMPRESS_EXT):
        nice_source = source[: -len(COMPRESS_EXT)]
        print(nice_source, "-->", folder)
        shutil.unpack_archive(source, "./" + folder)
        os.unlink(source)
    else:
        print(source, "-->", folder)
        shutil.move(source, ".")


def _find_restore_match(folder):
    archive_dir = get_archive_dir()
    pattern = os.path.join(archive_dir, "*", "*", folder)
    matches = glob.glob(pattern)
    if not matches:
        # try compressed
        pattern = os.path.join(archive_dir, "*", "*", folder + COMPRESS_EXT)
        matches = glob.glob(pattern)

        if not matches:
            bail("no project matches: " + folder)

    if len(matches) > 1:
        print("Warning: multiple matches, picking the most recent", file=sys.stderr)

    source = sorted(matches)[-1]

    return source


main.add_command(archive)
main.add_command(list)
main.add_command(restore)


if __name__ == "__main__":
    main()
