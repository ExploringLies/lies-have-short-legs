# -*- coding: utf-8 -*-
# <nbformat>4</nbformat>

# <codecell>

import csv
import json
import logging
import warnings

from pathlib import Path
import pandas as pd


def nodes_in_path(path, with_dirs=False, with_files=True):
    ret_val = []
    if with_dirs:
        ret_val += [p for p in Path(path).iterdir() if is_dir(p)]

    if with_files:
        ret_val += [p for p in Path(path).iterdir() if is_file(p)]

    return ret_val


def is_dir(path):
    return Path(path).is_dir()


def is_file(path):
    return Path(path).is_file()


def read_json(file_path, default_values=None):
    if is_file(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    else:
        warnings.warn('No such file found. {0} Returning given default_values'.format(file_path))
        return default_values


def dump_json(file_path, obj):
    with open(file_path, 'w') as f:
        return json.dump(obj, f)


def make_dir(path):
    Path(path).mkdir(parents=True)


def make_parent(path):
    p = Path(path).parent

    if not is_dir(p):
        p.mkdir(parents=True)


def parent(path):
    return Path(path).parent


def read_or_persist_as_pickle(fn, path, force_execution: bool=False):
    if is_file(path) and not force_execution:
        logging.debug('reading file {0} from file system'.format(path))
        return pd.read_pickle(path)

    logging.debug('executing function for file {0}, and storing it to file system'.format(path))
    val = fn()
    make_parent(path)
    val.to_pickle(path)
    return val


def remove(path):
    Path(path).unlink()


def write(file_path, content):
    """Write the content to the file!
    A parent directoy will be created."""
    make_parent(file_path)
    with open(file_path, 'w') as f:
        f.write(content)

