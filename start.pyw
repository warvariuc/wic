#!/usr/bin/env python3

import sys

try:
    sys.argv.remove('--debug')
except ValueError:
    _toProfile = False
else:
    _toProfile = True

from wic import w_app
import papp

app = w_app.WApp(sys.argv, papp.MainWindow)


if _toProfile:
    import cProfile, pstats
    cProfile.run('app.exec()', '.stats')

    stats = pstats.Stats('.stats')
    stats.sort_stats('cum', 'time')
    stats.print_stats(20)
else:
    app.exec()