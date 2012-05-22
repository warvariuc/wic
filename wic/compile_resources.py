#!/usr/bin/env python3

# delete all *.pyc files
# convert *.qrc files to *_rc.pyc files
# convert *.ui files to ui_*.pyc files
# Works on Windows and Linux (Ubuntu)
# part of the script is taken from makepyqt.pyw

import os, sys, stat
import subprocess, py_compile
from PyQt4 import QtGui



def build(path, recurse, removeSource= True):
    _apply(_build, path, recurse, removeSource= removeSource)
    #_apply(_translate, path, recurse)


def clean(path, recurse):
    _apply(_clean, path, recurse)


def _apply(function, path, recurse, **kwargs):
    for dirPath, dirs, files in os.walk(path):
        for fileName in files:
            function(dirPath, fileName, **kwargs)

def _build(dirPath, fileName, removeSource= True):
    if fileName.endswith(".ui"):
        targetName = "ui_%s.py" % fileName[:-3]
        command = pyuic4
    elif fileName.endswith(".qrc"):
        targetName = fileName[:-4] + "_rc.py"
        command = pyrcc4
    else:
        return
    source = os.path.join(dirPath, fileName)
    target = os.path.join(dirPath, targetName)

    args = ["-o", target, source]
    if command == pyrcc4:
        args.insert(0, "-py3")
        
    try:
        command += ' ' + ' '.join(args)
        output = subprocess.check_output(command, shell= True, stderr= subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print('Failed:', e.output)
    else:
        print('Converted %s to %s' % (source, targetName))

    if removeSource:
        # convert *.py to *.pyc and delete the source
        source = target
        target = source + 'c' # py -> pyc
        
        py_compile.compile(source, target)
        print('Compiled %s' % target)
    
        os.remove(source)
        print('Deleted source %s' % source)

def _clean(dirPath, fileName):
    if fileName.endswith('.pyc'):
        filePath = os.path.join(dirPath, fileName)
        os.remove(filePath)
        print('Deleted %s' % filePath)


#def _translate(self, path):
#    prefix = self.pathLabel.text()
#    if not prefix.endswith(os.sep):
#        prefix += os.sep
#    files = []
#    tsfiles = []
#    for name in os.listdir(path):
#        if name.endswith((".py", ".pyw")):
#            files.append(os.path.join(path, name))
#        elif name.endswith(".ts"):
#            tsfiles.append(os.path.join(path, name))
#    if not tsfiles:
#        return
#    settings = QSettings()
#    pylupdate4 = settings.value("pylupdate4", PYLUPDATE4)
#    lrelease = settings.value("lrelease", LRELEASE)
#    process = QProcess()
#    failed = 0
#    for ts in tsfiles:
#        qm = ts[:-3] + ".qm"
#        command1 = pylupdate4
#        args1 = files + ["-ts", ts]
#        command2 = lrelease
#        args2 = ["-silent", ts, "-qm", qm]
#        msg = "updated <font color=blue>{}</font>".format(
#                ts.replace(prefix, ""))
#        if self.debugCheckBox.isChecked():
#            msg = "<font color=green># {}</font>".format(msg)
#        else:
#            process.start(command1, args1)
#            if not process.waitForFinished(2 * 60 * 1000):
#                msg = self._make_error_message(command1, process)
#                failed += 1
#        self.logBrowser.append(msg)
#        msg = "generated <font color=blue>{}</font>".format(
#                qm.replace(prefix, ""))
#        if self.debugCheckBox.isChecked():
#            msg = "<font color=green># {}</font>".format(msg)
#        else:
#            process.start(command2, args2)
#            if not process.waitForFinished(2 * 60 * 1000):
#                msg = self._make_error_message(command2, process)
#                failed += 1
#        print(msg)
#    if failed:
#        print("{} files failed".format(failed))




Windows = sys.platform.lower().startswith(('win', 'microsoft'))

curDir = os.path.dirname(os.path.abspath(__file__))
PATH = QtGui.QApplication([]).applicationDirPath()

if Windows:
    PATH = os.path.join(os.path.dirname(sys.executable), 'Lib/site-packages/PyQt4')
    _path = os.path.join(PATH, 'bin')
    if os.access(_path, os.R_OK):
        PATH = _path

PYUIC4 = os.path.join(PATH, 'pyuic4')
PYRCC4 = os.path.join(PATH, 'pyrcc4')
PYLUPDATE4 = os.path.join(PATH, 'pylupdate4')
LRELEASE = 'lrelease'
if Windows:
    PYUIC4 = PYUIC4.replace('/', '\\') + '.bat'
    PYRCC4 = PYRCC4.replace('/', '\\') + '.exe'
    PYLUPDATE4 = PYLUPDATE4.replace('/', '\\') + '.exe'

pyuic4 = PYUIC4
pyrcc4 = PYRCC4

print('Be aware that some IDEs might automatically delete the resulting *.pyc files.\n')

clean(curDir, recurse= True)
build(curDir, recurse= True, removeSource= False)
