#!/usr/bin/env python3
import sys

import wic

import app


app = wic.app.App(sys.argv, app.MainWindow)
app.exec()
