import sys, os
from PyQt4 import QtCore, QtGui


try: # monkeypatch: use cdecimal if present instead of decimal = it is faster
    import cdecimal
    sys.modules['decimal'] = cdecimal 
except ImportError: 
    pass

from wic import w_app, w_main_window


def exception_hook(excType, excValue, excTraceback): # Global function to catch unhandled exceptions (mostly in user modules)
    import traceback
    info = ''.join (traceback.format_exception(excType, excValue, excTraceback))
    print(info)
#    import inspect
#    records = inspect.getinnerframes(exc_traceback) # http://docs.python.org/dev/library/inspect.html#inspect.getinnerframes
#    info = '<b>Произошло исключение</b>. История вызовов:\n'
#    for frame, file, lnum, func, lines, index in records:
#        info = info + '&nbsp;&nbsp;' \
#            'Файл "<span style="background-color:#EDEFF4"> ' + file + ' </span>", ' \
#            'строка <span style="background-color:#EDEFF4">&nbsp;' + str(lnum) + ' </span>, ' \
#            'функция <span style="background-color:#EDEFF4">&nbsp;' + func + ' </span>' \
#            '\n&nbsp;<span style="color:maroon">&nbsp;' + lines[0] + ' </span>'
#    info = info + '<br>Описание ошибки: <span style="background-color:#EDEFF4">&nbsp;' + exc_type.__name__ + ' </span>: ' \
#        '<span style="color:maroon">&nbsp;' + str(exc_value).replace('\n', '\n&nbsp;') + '</span>'

    QtGui.qApp.mainWindow.messagesWindow.printMessage(info)

sys.excepthook = exception_hook # set our exception hook

#sys.path.append(os.path.join(appDir, 'widgets')) # path for searching resources and custom widgets modules

def loadTestConf(): # load default test configuration
    #from wic import w
    #w.loadConf(os.path.join(QtGui.qApp.appDir, '..', 'conf/'))
    from conf.reports import lissajous as test
    form = test.Form(None) # no parent widget for now
    window = mainWindow.mdiArea.addSubWindow(form) # create subwindow with the form
    form.closed.connect(window.close)


app = w_app.WApp(sys.argv)
appDir = QtGui.qApp.appDir = os.path.dirname(os.path.abspath(__file__))


mainWindow = QtGui.qApp.mainWindow = w_main_window.WMainWindow()
mainWindow.show()


QtCore.QTimer.singleShot(0, loadTestConf) # когда начнет работать очередь сообщений - загрузить тестовую конфигурацию

app.exec() # start the event loop
