#!/usr/bin/env python3

"""
convert *.qrc files to *_rc.pyc files
convert *.ui files to ui_*.pyc files
"""

import os
import sys
import subprocess
import py_compile

from PyQt5 import QtWidgets


PYUIC = 'pyuic5'
PYRCC = 'pyrcc5'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def build(path, recurse, remove_source=True):
    _apply(_build, path, recurse, remove_source=remove_source)


def _apply(function, path, recurse, **kwargs):
    for dir_path, dirs, files in os.walk(path):
        for file_name in files:
            function(dir_path, file_name, **kwargs)


def _build(dir_path, file_name, remove_source=True):
    if file_name.endswith(".ui"):
        target_name = "ui_%s.py" % file_name[:-3]
        command = PYUIC
    elif file_name.endswith(".qrc"):
        target_name = file_name[:-4] + "_rc.py"
        command = PYRCC
    else:
        return
    source = os.path.join(dir_path, file_name)
    target = os.path.join(dir_path, target_name)

    args = ["-o", target, source]
    try:
        command += ' ' + ' '.join(args)
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print('Failed:', e.output)
    else:
        print('Converted %s to %s' % (source, target_name))

    if remove_source:
        # convert *.py to *.pyc and delete the source
        source = target
        target = source + 'c'  # py -> pyc

        py_compile.compile(source, target)
        print('Compiled %s' % target)

        os.remove(source)
        print('Deleted source %s' % source)


def _clean(dir_path, file_name):
    if file_name.endswith('.pyc'):
        file_path = os.path.join(dir_path, file_name)
        os.remove(file_path)
        print('Deleted %s' % file_path)


build(BASE_DIR, recurse=True, remove_source=False)
