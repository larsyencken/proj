# -*- coding: utf-8 -*-
#
#  test_config.py
#  proj
#

"""
"""

from tempfile import NamedTemporaryFile

from proj import Config


def test_read_write_config():
    with NamedTemporaryFile() as f:
        filename = f.name

        config = Config(
            compression=True, compression_format="cheese", archive_dir="craZyNaME"
        )
        config.save(filename)

        assert Config.load(filename) == config
