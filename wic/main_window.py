import html
import sys
import traceback

from PyQt5 import QtCore, QtGui, QtWidgets


class MainWindow(QtWidgets.QMainWindow):

    _window_icon = ':/icons/fugue/leaf-plant.png'
    _window_title = 'wic'
    _authentication_enabled = True
    # whether to allow unconditional quit (if some forms didn't close)
    _unconditional_quit = True

    def __init__(self, parent = None):
        super().__init__(parent)

        self.setWindowTitle(self._window_title)
        self.setWindowIcon(QtGui.QIcon(self._window_icon))

        mdi_area = QtWidgets.QMdiArea()
        mdi_area.setDocumentMode(True)
        mdi_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        mdi_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        mdi_area.setViewMode(mdi_area.TabbedView)
        mdi_area.setTabPosition(QtWidgets.QTabWidget.North)
        mdi_area.setActivationOrder(mdi_area.ActivationHistoryOrder)
        mdi_area.subWindowActivated.connect(self.onSubwindowActivated)
        self.setCentralWidget(mdi_area)
        self.mdi_area = mdi_area

        # hack: http://www.qtforum.org/article/31711/close-button-on-tabs-of-mdi-windows-qmdiarea-qmdisubwindow-workaround.html
        tab_bar = mdi_area.findChildren(QtWidgets.QTabBar)[0]
        tab_bar.setTabsClosable(True)
        tab_bar.setExpanding(False)
        tab_bar.setMovable(True)
        tab_bar.setDrawBase(True)
        #tab_bar.setShape(tabBar.TriangularSouth)
        #tab_bar.setIconSize(QtCore.QSize(16, 16))
        self.tabBar = tab_bar

        tab_bar_event_filter = TabBarEventFilter(self)
        tab_bar.installEventFilter(tab_bar_event_filter)

        self.statusBar() # create status bar

        self.messagesWindow = messages_window.MessagesWindow(self)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.messagesWindow)

        self.printMessage = self.messagesWindow.printMessage # not nice

        sys.stdout = MessagesOut(self.printMessage)  # hook the real STDOUT
        sys.excepthook = exception_hook # set our exception hook

        self.settings = settings.Settings(self)

        self.setupMenu()

        if self._authentication_enabled:
            self.authenticate()
        # when event loop is working
        QtCore.QTimer.singleShot(0, self.on_system_started)

    def setupMenu(self):
        self.menu = menus.MainMenu(self)

    def onSubwindowActivated(self, subWindow): # http://doc.trolltech.com/latest/qmdiarea.html#subWindowActivated
        #self.mdiArea.setActiveSubWindow(subWindow)
        saveActive = bool(subWindow and subWindow.isWindowModified())
        #self.fileSaveAction.setEnabled(saveActive)

    def onTabBarLeftDblClick(self):
        sub_window = self.mdi_area.currentSubWindow()
        if sub_window.isMaximized():
            sub_window.showNormal()
        else:
            sub_window.showMaximized()

    def closeEvent(self, event):
        self.mdi_area.closeAllSubWindows() # Passes a close event from main window to all subwindows.
        if self.mdi_area.subWindowList(): # there are still open subwindows
            event.ignore()
            return
        if self.on_system_about_to_quit() is False: # именно False, иначе None тоже считается отрицательным
            event.ignore()
            return
        self.settings.save()

    def restore_subwindows(self):
        for window in self.mdi_area.subWindowList():
            window.showNormal()

    def minimize_subwindows(self):
        for window in self.mdi_area.subWindowList():
            window.showMinimized()

    def add_subwindow(self, widget): # https://bugreports.qt.nokia.com/browse/QTBUG-9462
        """Add a new subwindow with the given widget
        """
        sub_window = QtWidgets.QMdiSubWindow() # no parent
        sub_window.setWidget(widget)
        sub_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.mdi_area.addSubWindow(sub_window)
        sub_window.setWindowIcon(widget.windowIcon())
        sub_window.show()
        if isinstance(widget, forms.Form):
            widget.closed.connect(sub_window.close) # when form closes - close subWindow too
        return sub_window

    def authenticate(self):
        """Ask for credentials and check if the user is allowed to enter the system.
        """

    def requestQuit(self, unconditional = False):
        """Request application quit.
        """
        #self._unconditionalQuit = unconditional
        # TODO: check for self._unconditionalQuit when closing forms and mainWindow
        self.close()

    def on_system_started(self):
        """Called on startup when everything is ready.
        """

    def on_system_about_to_quit(self):
        """Called when the app is requested to quit. Return False to cancel
        """

    def show_warning(self, title, text):
        """Convenience function to show a warning message box.
        """
        QtWidgets.QMessageBox.warning(self, title, text)

    def show_information(self, title, text):
        """Convenience function to show an information message box.
        """
        QtWidgets.QMessageBox.information(self, title, text)


class TabBarEventFilter(QtCore.QObject):
    """Event filter for main window's tab bar.
    """
    def eventFilter(self, tabBar, event):
        if event.type() == QtCore.QEvent.MouseButtonDblClick:
            if event.button() == QtCore.Qt.LeftButton:
                self.parent().onTabBarLeftDblClick()
                return True  # message processed
        return super().eventFilter(tabBar, event)  # standard event processing


def exception_hook(exc_type, exc_value, exc_traceback):
    """Global function to catch unhandled exceptions (mostly in user modules).
    """
    info = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print(info)


class MessagesOut():
    """Our replacement for stdout. It prints messages also the the messages window. 
    If txt does not start with '<>' it is escaped to be properly shown in QTextEdit.
    """
    def __init__(self, print_message_func):
        self.print_message = print_message_func

    def write(self, txt):
        print(txt, end='', file=sys.__stdout__)
        if not txt.startswith('<>'):
            txt = html.escape(txt)
        self.print_message(txt, end='')

    def flush(self):
        sys.__stdout__.flush()


from wic import messages_window
from wic import settings
from wic import forms
from wic import menus

