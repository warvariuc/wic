from PyQt4 import QtGui, QtCore
from wic.widgets import ui_w_popup_calendar
from datetime import date as Date, datetime as DateTime
from dateutil.relativedelta import relativedelta as RelDelta


class WCalendarPopup(QtGui.QWidget, ui_w_popup_calendar.Ui_WPopupCalendar):
    '''Popup window to select date interactively by showing a month calendar.'''
    def __init__(self, parent, persistent= False):
        if not parent: 
            persistent = True
        self.persistent = persistent
        super().__init__(parent, QtCore.Qt.Tool if persistent else QtCore.Qt.Popup)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose) # освобождать память - надо исследовать этот вопрос
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(':/icons/fugue/calendar-blue.png'))

        todayFormat = QtGui.QTextCharFormat()
        todayFormat.setFontWeight(QtGui.QFont.Bold)
        todayFormat.setFontUnderline(True)
        self.calendarWidget.setDateTextFormat(QtCore.QDate.currentDate(), todayFormat) # emphasize current date in calendar

        self.calendarWidget.activated.connect(self.accepted)
        #self.calendarWidget.clicked.connect(self.accepted)
        self.calendarWidget.currentPageChanged.connect(self.onCurrentPageChanged)
        self.calendarWidget.selectionChanged.connect(self.onSelectionChanged)
        self.nextMonth.clicked.connect(self.calendarWidget.showNextMonth)
        self.nextYear.clicked.connect(self.calendarWidget.showNextYear)
        self.prevMonth.clicked.connect(self.calendarWidget.showPreviousMonth)
        self.prevYear.clicked.connect(self.calendarWidget.showPreviousYear)
        self.date.clicked.connect(self.showMenu)
        
        if isinstance(parent, WDateEdit):
            parent.setFocus()
            self.selectDate(parent.currentDate())
        else:
            self.selectDate()
            
        self.calendarWidget.installEventFilter(self)
        for child in self.calendarWidget.findChildren(QtGui.QWidget):
            child.installEventFilter(self)

        self.positionPopup()
        self.calendarWidget.setFocus()

    def showMenu(self):
        menu = QtGui.QMenu(self)
        menu.addAction('Today', self.selectDate)
        menu.exec(QtGui.QCursor.pos())
        
    def selectDate(self, date= None):
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

    def onCurrentPageChanged(self, year,  month):
        months = (year - self.calendarWidget.selectedDate().year()) * 12 + month - self.calendarWidget.selectedDate().month()
        self.calendarWidget.setSelectedDate(self.calendarWidget.selectedDate().addMonths(months))

    def positionPopup(self): # taken from QtCore.QDatetimeedit.cpp
        parent = self.parent()
        if isinstance(parent, WDateEdit):
            pos = parent.mapToGlobal(parent.rect().bottomRight()) # bottom left corner of the lineedit widget
            screen = QtGui.QApplication.desktop().availableGeometry()
    
            y = pos.y()
            if y > screen.bottom() - self.height():
                y = parent.mapToGlobal(parent.rect().topLeft()).y() - self.height()
            
            pos.setX(max(screen.left(), min(screen.right() - self.width(), pos.x() - self.width())))
            pos.setY(max(screen.top(), y))
            self.move(pos)
        
    def accepted(self):
        if self.persistent: 
            return
        if isinstance(self.parent(), WDateEdit):
            qDate = self.calendarWidget.selectedDate()
            self.parent().setDate(Date(qDate.year(), qDate.month(), qDate.day()), emitEdited= True)
        self.close()
    
    def eventFilter(self, target, event): # target - calendarWidget or any of its children
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



class WDateEdit(QtGui.QLineEdit):
    "Custom widget for editing dates. Allows selecting a date using a popup calendar."
    
    edited = QtCore.pyqtSignal()
    
    def __init__(self, parent= None):
        super().__init__(parent)
        #self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setAlignment(QtCore.Qt.AlignRight)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        self.menu = QtGui.QMenu(self) # context menu
        self.menu.addAction(QtGui.QIcon(':/icons/fugue/calendar-blue.png'), 'Calendar', self.popupCalendar, QtGui.QKeySequence(QtCore.Qt.Key_Insert))
        self.menu.addAction(QtGui.QIcon(':/icons/fugue/document-copy.png'), 'Copy', self.copy, QtGui.QKeySequence(QtGui.QKeySequence.Copy))
        self.menu.addAction(QtGui.QIcon(':/icons/fugue/clipboard-paste.png'), 'Paste', self.paste, QtGui.QKeySequence(QtGui.QKeySequence.Paste))
        self.menu.addAction(QtGui.QIcon(':/icons/fugue/eraser.png'), 'Clear', self.clear)

        self.selector = QtGui.QToolButton(self)
        self.selector.setIcon(QtGui.QIcon(':/icons/fugue/calendar-blue.png'))
        self.selector.setCursor(QtCore.Qt.PointingHandCursor)
        self.selector.setStyleSheet('QToolButton { border: none; padding: 0px; }')
        self.selector.setFocusPolicy(QtCore.Qt.NoFocus)

        self.selector.clicked.connect(self.popupCalendar)
        self.textChanged.connect(self.onTextChanged)

        self.setSelectorVisible(True) # cause style recalculation
        self.setDate(None)

    def resizeEvent(self, event):
        sz = self.selector.sizeHint()
        frameWidth = self.style().pixelMetric(QtGui.QStyle.PM_DefaultFrameWidth)
        self.selector.move(self.rect().right() - frameWidth - sz.width(),
                      (self.rect().bottom() + 1 - sz.height()) / 2)
                      
    def isSelectorVisible(self):
        return not self.selector.isHidden() # notice that isVisible() is not used (because widget can be non visible but not hidden)        
    def setSelectorVisible(self, value):
        self.selector.setVisible(value)
        borderWidth = self.style().pixelMetric(QtGui.QStyle.PM_DefaultFrameWidth) + 1
        paddingRight = borderWidth + (self.selector.sizeHint().width() if value else 0)
        self.setStyleSheet('QLineEdit { padding-right: %dpx; }' % paddingRight)
        fm = QtGui.QFontMetrics(self.font()) # font metrics
        self.setMinimumSize(fm.width('99.99.9999') + self.selector.sizeHint().height() + borderWidth * 2,
                max(fm.height(), self.selector.sizeHint().height() + borderWidth * 2))
    selectorVisible = QtCore.pyqtProperty(bool, isSelectorVisible, setSelectorVisible)

    def onTextChanged(self, txt):
        txt = list(str(txt))
        curPos = self.cursorPosition()
        i = 0
        while i < len(txt):
            char = txt[i]
            if not (char.isdigit() or char == ' '): 
                del txt[i]
                if i < curPos: 
                    curPos -= 1 # курсор должен находится все после той же цифры
            else: 
                i += 1
        len_ = 8 # standard length '__.__.____'
        fstPart = txt[:min(curPos, len_)]
        lstPart = txt[max(len(fstPart), len(txt) - len_ + len(fstPart)): len(txt)]
        midPart = [' ' for i in range(len_ - len(fstPart) - len(lstPart))]
        a = ''.join(fstPart + midPart + lstPart)
        self.setText(a[0:2] + '.' + a[2:4] + '.' + a[4:])
        if curPos > 4:
            curPos += 2 # поправка курсора из-за вставленной точки
        elif curPos > 2:
            curPos += 1
        self.setCursorPosition(curPos)

    def mouseDoubleClickEvent(self, mouseEvent):
        if mouseEvent.button() == QtCore.Qt.LeftButton:
            self.selectAll () # select all on double click, otherwise only group of digits will be selected
            
    def keyPressEvent(self, keyEvent):
        key = keyEvent.key()
        if keyEvent.modifiers() in (QtCore.Qt.NoModifier, QtCore.Qt.KeypadModifier):
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
                self.applyCurrentDate(force= True)
                return
            elif key == QtCore.Qt.Key_Left:
                if self.hasSelectedText():
                    self.setCursorPosition(self.selectionStart()) # переместим курсор на начало выделения - чтобы было удобнее
        super().keyPressEvent(keyEvent)

    def focusOutEvent(self, focusEvent):
        'Check for changes when leaving the widget'
        if focusEvent.reason() != QtCore.Qt.PopupFocusReason: # контекстное меню выскочило или еще что
            self.applyCurrentDate()
        super().focusOutEvent(focusEvent)
    
    def wheelEvent(self, wheelEvent):
        if not self.hasFocus(): 
            return # only on focused widget
        self.setCursorPosition(self.cursorPositionAt(wheelEvent.pos()))
        self.addDays(int(wheelEvent.delta() / 120))
        wheelEvent.ignore()

    def addDays(self, number): # target - lineEdit
        curPos = self.cursorPosition()
        date = self.currentDate()
        if date: # empty or malformed date
            if curPos <= 2: # day was 'wheeled'
                self.setText((date + RelDelta(days= number)).strftime('%d.%m.%Y'))
                self.setSelection(0, 2)
            elif curPos <= 5: # month was 'wheeled'
                self.setText((date + RelDelta(months= number)).strftime('%d.%m.%Y'))
                self.setSelection(3, 2)
            else: # year was 'wheeled'
                self.setText((date + RelDelta(years= number)).strftime('%d.%m.%Y'))
                self.setSelection(6, 4)
            
    def popupCalendar(self):
        self.selectAll()
        WCalendarPopup(self).show()

    def getDate(self): 
        return self._date
    def setDate(self, value, emitEdited= False):
        if value is None:
            strValue = '  .  .    '
        elif isinstance(value, Date):
            strValue = value.strftime('%d.%m.%Y')
        else:
            raise Exception('Value must a datetime.date or None.')
        self._date = value
        self.setText(strValue)
        self.setCursorPosition(0)
        if emitEdited:
            self.edited.emit()
    date = QtCore.pyqtProperty(Date, getDate, setDate)
    
    #setMinimumDate
    #setMaximumDate

    def currentDate(self, text= ''): # interpret entered string as date
        text = text or self.text()
        try:
            datetime = DateTime.strptime(text, '%d.%m.%Y')
        except ValueError:
            return None
        return datetime.date()

    def applyCurrentDate(self, force= False):
        curDate = self.currentDate()
        if self._date != curDate or force:
            self.setDate(curDate, emitEdited= True)
#        if not currentValue:
#            for char in self.text():
#                if char.isdigit():
#                    self.setStyleSheet('QLineEdit { background-color: yellow }')
#                    return
#        self.setStyleSheet('QLineEdit { background-color: white }')

    def contextMenuEvent(self, qContextMenuEvent):
        self.selectAll()
        self.menu.popup(qContextMenuEvent.globalPos())

            


if __name__ == '__main__': # some tests
    app = QtGui.QApplication([])
    widget = WDateEdit(None)
    widget.show()
    app.exec()
