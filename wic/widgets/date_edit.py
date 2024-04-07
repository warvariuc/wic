from PyQt5 import QtGui, QtCore, QtWidgets, QtWidgets

from wic.datetime import RelDelta, Date, DateTime
from . import ui_popup_calendar


class CalendarPopup(QtWidgets.QWidget, ui_popup_calendar.Ui_PopupCalendar):
    """Popup window to select date interactively by showing a month calendar.
    """
    def __init__(self, parent, persistent = False):
        if not parent:
            persistent = True
        self.persistent = persistent
        super().__init__(parent, QtCore.Qt.Tool if persistent else QtCore.Qt.Popup)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(':/icons/fugue/calendar-blue.png'))

        todayFormat = QtGui.QTextCharFormat()
        todayFormat.setFontWeight(QtGui.QFont.Bold)
        todayFormat.setFontUnderline(True)
        # emphasize current date in calendar
        self.calendarWidget.setDateTextFormat(QtCore.QDate.currentDate(), todayFormat)

        self.calendarWidget.activated.connect(self.accepted)
        #self.calendarWidget.clicked.connect(self.accepted)
        self.calendarWidget.currentPageChanged.connect(self.onCurrentPageChanged)
        self.calendarWidget.selectionChanged.connect(self.onSelectionChanged)
        self.nextMonth.clicked.connect(self.calendarWidget.showNextMonth)
        self.nextYear.clicked.connect(self.calendarWidget.showNextYear)
        self.prevMonth.clicked.connect(self.calendarWidget.showPreviousMonth)
        self.prevYear.clicked.connect(self.calendarWidget.showPreviousYear)
        self.date.clicked.connect(self.showMenu)

        if isinstance(parent, DateEdit):
            parent.setFocus()
            self.selectDate(parent.date())
        else:
            self.selectDate()

        self.calendarWidget.installEventFilter(self)
        for child in self.calendarWidget.findChildren(QtWidgets.QWidget):
            child.installEventFilter(self)

        self.positionPopup()
        self.calendarWidget.setFocus()

    def showMenu(self):
        menu = QtWidgets.QMenu(self)
        menu.addAction('Today', self.selectDate)
        menu.exec(QtGui.QCursor.pos())

    def selectDate(self, date = None):
        if isinstance(date, QtCore.QDate):
            pass
        elif isinstance(date, Date):
            date = QtCore.QDate(date.year, date.month, date.day)
        else:
            date = QtCore.QDate.currentDate()
        self.calendarWidget.setSelectedDate(date)
        self.onSelectionChanged()

    def onSelectionChanged(self):
        self.date.setText(self.calendarWidget.selectedDate().toString('dd MMM yyyy'))

    def onCurrentPageChanged(self, year, month):
        months = (year - self.calendarWidget.selectedDate().year()) * 12 + \
                 month - self.calendarWidget.selectedDate().month()
        self.calendarWidget.setSelectedDate(self.calendarWidget.selectedDate().addMonths(months))

    def positionPopup(self):
        # as in QtCore.QDatetimeedit.cpp
        parent = self.parent()
        if isinstance(parent, DateEdit):
            # bottom left corner of the lineedit widget
            pos = parent.mapToGlobal(parent.rect().bottomRight())
            screen = QtWidgets.QApplication.desktop().availableGeometry()

            y = pos.y()
            if y > screen.bottom() - self.height():
                y = parent.mapToGlobal(parent.rect().topLeft()).y() - self.height()

            pos.setX(max(screen.left(), min(screen.right() - self.width(), pos.x() - self.width())))
            pos.setY(max(screen.top(), y))
            self.move(pos)

    def accepted(self):
        if self.persistent:
            return
        if isinstance(self.parent(), DateEdit):
            qDate = self.calendarWidget.selectedDate()
            self.parent().setDate(Date(qDate.year(), qDate.month(), qDate.day()), emit = True)
        self.close()

    def eventFilter(self, target, event):
        # target - calendarWidget or any of its children
        if event.type() == QtCore.QEvent.KeyPress:
            key = event.key()
            if event.modifiers() in (QtCore.Qt.NoModifier, QtCore.Qt.KeypadModifier):
                if key in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):
                    if not self.persistent:
                        self.accepted()
                        return True
                elif key in (QtCore.Qt.Key_Escape, QtCore.Qt.Key_Insert):
                    if not self.persistent:
                        self.close()
                        return True
                if key == QtCore.Qt.Key_PageDown:
                    self.nextMonth.animateClick()
                    return True
                if key == QtCore.Qt.Key_PageUp:
                    self.prevMonth.animateClick()
                    return True
            elif event.modifiers() in (QtCore.Qt.ControlModifier, QtCore.Qt.ShiftModifier):
                if key == QtCore.Qt.Key_PageDown:
                    self.nextYear.animateClick()
                    return True
                elif key == QtCore.Qt.Key_PageUp:
                    self.prevYear.animateClick()
                    return True
        elif event.type() == QtCore.QEvent.MouseButtonPress:
            if event.button() == QtCore.Qt.RightButton:
                self.date.animateClick()
                return True
        return super().eventFilter(target, event) # standard event processing        



class DateEdit(QtWidgets.QLineEdit):
    """Custom widget for editing dates. Allows selecting a date using a popup calendar.
    """

    edited = QtCore.pyqtSignal()

    def __init__(self, parent = None):
        super().__init__(parent)
        #self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setAlignment(QtCore.Qt.AlignRight)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        self.menu = QtWidgets.QMenu(self) # context menu
        self.menu.addAction(
            QtGui.QIcon(':/icons/fugue/calendar-blue.png'), 'Calendar',
            self.popupCalendar, QtGui.QKeySequence(QtCore.Qt.Key_Insert))
        self.menu.addAction(
            QtGui.QIcon(':/icons/fugue/document-copy.png'), 'Copy',
            self.copy, QtGui.QKeySequence(QtGui.QKeySequence.Copy))
        self.menu.addAction(
            QtGui.QIcon(':/icons/fugue/clipboard-paste.png'), 'Paste',
            self.paste, QtGui.QKeySequence(QtGui.QKeySequence.Paste))
        self.menu.addAction(
            QtGui.QIcon(':/icons/fugue/eraser.png'), 'Clear', self.interactiveClear)

        self.selector = QtWidgets.QToolButton(self)
        self.selector.setIcon(QtGui.QIcon(':/icons/fugue/calendar-blue.png'))
        self.selector.setCursor(QtCore.Qt.PointingHandCursor)
        self.selector.setStyleSheet('QToolButton { border: none; padding: 0px; }')
        self.selector.setFocusPolicy(QtCore.Qt.NoFocus)

        self.selector.clicked.connect(self.popupCalendar)
        self.textEdited.connect(self.onTextEdited)

        self.selectorVisible = True  # cause style recalculation
        self._prev_text = None # is used to track editing
        self.setDate(None)

    def resizeEvent(self, event):
        sz = self.selector.sizeHint()
        frameWidth = self.style().pixelMetric(QtWidgets.QStyle.PM_DefaultFrameWidth)
        self.selector.move(self.rect().right() - frameWidth - sz.width(),
                      (self.rect().bottom() + 1 - sz.height()) / 2)

    def isSelectorVisible(self):
        # notice that isVisible() is not used (because widget can be non visible but not hidden)
        return not self.selector.isHidden()
    def setSelectorVisible(self, value):
        self.selector.setVisible(value)
        borderWidth = self.style().pixelMetric(QtWidgets.QStyle.PM_DefaultFrameWidth) + 1
        selectorWidth = borderWidth + (self.selector.sizeHint().width() if value else 0)
        self.setStyleSheet('QLineEdit { padding-right: %ipx; }' % selectorWidth)
        fm = QtGui.QFontMetrics(self.font()) # font metrics
        self.setMinimumSize(fm.width('99.99.9999 ') + borderWidth * 2 + selectorWidth,
                max(fm.height(), self.selector.sizeHint().height() + borderWidth * 2))
    selectorVisible = QtCore.pyqtProperty(bool, isSelectorVisible, setSelectorVisible)

    def date(self):
        """Return the date entered in the field. If it is empty or invalid - `None` is returned.
        """
        try:
            return DateTime.strptime(self.text(), '%d.%m.%Y').date()
        except ValueError:
            return None

    def setDate(self, value, emit=False):
        """Set field text for the given date.

        Args:
            value: the date to set. `None` - empty date.
            emit (bool): whether to emit `edited` signal (like when the date is entered
                interactively)
        """
        if value is None:
            strValue = '  .  .    '
        elif isinstance(value, Date):
            strValue = value.strftime('%d.%m.%Y')
        else:
            raise TypeError('Value must a `datetime.date` or `None`.')
        self.setText(strValue)
        self.setCursorPosition(0)
        if emit:
            self.edited.emit()

    #setMinimumDate
    #setMaximumDate

    def interactiveClear(self):
        self.clear()
        self.onTextEdited('')

    def clear(self):
        self.setDate(None)

    def onTextEdited(self, text):
        """Called whenever the text is edited interactively (not programmatically like via
        setText()). Filters non digits or space entered symbols.
        """
        text = list(str(self.text()))
        cursor_pos = self.cursorPosition()
        i = 0
        while i < len(text):
            # remove invalid symbols
            if text[i].isdigit():
                i += 1
            else:
                del text[i]
                # the cursor has to stay after the same digit
                cursor_pos -= int(i < cursor_pos)

        len_ = 8  # standard length '__.__.____'
        first_part = text[:min(cursor_pos, len_)]
        last_part = text[max(len(first_part), len(text) - len_ + len(first_part)):]
        mid_part = [' '] * (len_ - len(first_part) - len(last_part))
        a = ''.join(first_part + mid_part + last_part)
        self.setText(a[0:2] + '.' + a[2:4] + '.' + a[4:])
        if cursor_pos >= 4:
            cursor_pos += 2  # take into account the dot
        elif cursor_pos >= 2:
            cursor_pos += 1
        self.setCursorPosition(cursor_pos)
        if self._prev_text is None:
            # start of editing
            self._prev_text = self.text()

    def focusOutEvent(self, focusEvent):
        """Check for changes when leaving the widget
        """
        if focusEvent.reason() != QtCore.Qt.PopupFocusReason:
            # context menu (or smth else)
            if self._prev_text is not None:
                # while the widget was focused - the text was changed
#                if self.date() is None: # invalid date
#                    self.setDate(None)
                self.edited.emit()
                self._prev_text = None  # reset the tracking
        super().focusOutEvent(focusEvent)

    def mouseDoubleClickEvent(self, mouseEvent):
        if mouseEvent.button() == QtCore.Qt.LeftButton:
            # select all on double click, otherwise only group of digits will be selected
            self.selectAll()

    def keyPressEvent(self, keyEvent):
        if keyEvent.modifiers() in (QtCore.Qt.NoModifier, QtCore.Qt.KeypadModifier):
            key = keyEvent.key()
            if key == QtCore.Qt.Key_Insert:
                self.popupCalendar()
                return
            elif key == QtCore.Qt.Key_Down:
                self.addDays(-1)
                return
            elif key == QtCore.Qt.Key_Up:
                self.addDays(1)
                return
            elif key in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):
                self.edited.emit()  # forcibly emit edited signal
                return
            elif key == QtCore.Qt.Key_Left:
                if self.hasSelectedText():
                    # move cursor to the beginning of the selection, to be more comfortable
                    self.setCursorPosition(self.selectionStart())
                    return
            elif key in (QtCore.Qt.Key_Backspace, QtCore.Qt.Key_Delete) and not self.hasSelectedText():
                text = self.text()
                cursor_pos = self.cursorPosition()
                if key == QtCore.Qt.Key_Backspace:
                    pos_del = cursor_pos - 1  # position to check for character
                    pos_move = cursor_pos - 1  # position to move to
                else:  # key == QtCore.Qt.Key_Delete:
                    pos_del = cursor_pos
                    pos_move = cursor_pos + 1
                if 0 <= pos_del < len(text):
                    char_del = text[pos_del]
                    if char_del == '.':  # the char to be deleted is a dot
                        self.setCursorPosition(pos_move)  # jump over the char
        super().keyPressEvent(keyEvent)

    def wheelEvent(self, wheelEvent):
        if not self.hasFocus():
            return  # only on focused widget
        self.setCursorPosition(self.cursorPositionAt(wheelEvent.pos()))
        self.addDays(int(wheelEvent.delta() / 120))
        wheelEvent.accept()

    def addDays(self, number):
        # target - lineEdit
        cursor_pos = self.cursorPosition()
        date = self.date()
        if date:  # empty or malformed date
            if cursor_pos <= 2:  # day was 'wheeled'
                new_date = date + RelDelta(days = number)
                selection = (0, 2)
            elif cursor_pos <= 5:  # month was 'wheeled'
                new_date = date + RelDelta(months = number)
                selection = (3, 2)
            else:  # year was 'wheeled'
                new_date = date + RelDelta(years = number)
                selection = (6, 4)
            new_text = new_date.strftime('%d.%m.%Y')
            self.setText(new_text)
            self.textEdited.emit(new_text)  # kind of interactive edit
            self.setSelection(*selection)

    def contextMenuEvent(self, qContextMenuEvent):
        self.selectAll()
        self.menu.popup(qContextMenuEvent.globalPos())

    def popupCalendar(self):
        self.selectAll()
        CalendarPopup(self).show()


if __name__ == '__main__':  # some tests
    app = QtWidgets.QApplication([])
    widget = DateEdit(None)
    widget.show()
    app.exec()
