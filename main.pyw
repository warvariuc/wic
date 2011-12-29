#!/usr/bin/env python3

import sys
from papp import App

try:
    sys.argv.remove('--debug')
except ValueError:
    _toProfile = False
else:
    _toProfile = True

app = App(sys.argv)


if _toProfile:
    import cProfile, pstats
    cProfile.run('app.exec()', '.stats')

    stats = pstats.Stats('.stats')
    stats.sort_stats('cum', 'time')
    stats.print_stats(20)
else:
    app.exec()