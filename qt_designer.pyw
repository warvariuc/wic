#!/usr/bin/env python3
# coding: utf-8

import os, sys, subprocess

params = sys.argv[:]
home_path = os.path.dirname(os.path.abspath(params[0]))
params[0] = 'designer' # "designer-qt4" on Linux

# add search path for custom widgets and plugins for designer
os.putenv('PYQTDESIGNERPATH', os.path.join(home_path, 'widgets'))
os.putenv('PATH', os.getenv('PATH', '') + ';' + os.path.dirname(sys.executable)) # http://code.activestate.com/recipes/577233-adding-the-directory-of-the-python-executable-to-t/

retcode = subprocess.Popen(params)


"""
http://www.riverbankcomputing.co.uk/static/Docs/PyQt4/pyqt4ref.html#writing-qt-designer-plugins
>The PYQTDESIGNERPATH environment variable specifies the set of directories to search for plugins.
Directory names are separated by a path separator (a semi-colon on Windows and a colon on other platforms).
If a directory name is empty (ie. there are consecutive path separators or a leading or trailing path
separator) then a set of default directories is automatically inserted at that point.
The default directories are the python subdirectory of each directory that Designer
searches for its own plugins. If the environment variable is not set then only the default
directories are searched. If a file's basename does not end with plugin then it is ignored.
"""
