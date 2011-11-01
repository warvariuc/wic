from PyQt4 import QtGui, QtCore
from wic.widgets.w_date import Date
from wic.widgets import ui_w_popup_calendar


class WCalendarPopup(QtGui.QWidget, ui_w_popup_calendar.Ui_WPopupCalendar):
    "Popup window to select date interactively by showing a month calendar."
    def __init__(self, parent, persistent=False):
        if not parent: persistent = True
        super().__init__(parent, QtCore.Qt.Tool if persistent else QtCore.Qt.Popup)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose) # освобождать память - надо исследовать этот вопрос
        self.setupUi(self)
        self.persistent = persistent

        todayFormat = QtGui.QTextCharFormat()
        todayFormat.setFontWeight(QtGui.QFont.Bold)
        todayFormat.setFontUnderline(True)
        self.calendarWidget.setDateTextFormat(QtCore.QDate.currentDate(), todayFormat) # emphasize current date in calendar

        self.calendarWidget.activated.connect(self.accepted)
        self.calendarWidget.clicked.connect(self.accepted)
        self.calendarWidget.currentPageChanged.connect(self.currentPageChanged)
        self.calendarWidget.selectionChanged.connect(self.selectionChanged)
        self.nextMonth.clicked.connect(self.calendarWidget.showNextMonth)
        self.nextYear.clicked.connect(self.calendarWidget.showNextYear)
        self.prevMonth.clicked.connect(self.calendarWidget.showPreviousMonth)
        self.prevYear.clicked.connect(self.calendarWidget.showPreviousYear)
        self.date.clicked.connect(self.showMenu)
        
        if isinstance(parent, WDateEdit):
            parent.setFocus()
            self.selectDate(parent.currentValue())
        else:
            self.selectDate()
            
        self.calendarWidget.installEventFilter(self)
        for child in self.calendarWidget.findChildren(QtGui.QWidget):
            child.installEventFilter(self)

        self.positionPopup()
        self.calendarWidget.setFocus()

    def showMenu(self):
        menu = QtGui.QMenu(self)
        menu.addAction('Сегодня', self.selectDate)
        menu.exec(QtGui.QCursor.pos())
        
    def selectDate(self, d=None):
        if isinstance(d, QtCore.QDate):
            pass
        elif isinstance(d, Date) and d:
            d = QtCore.QDate(d.year(), d.month(), d.day())
        else:
            d = QtCore.QDate.currentDate()
        self.calendarWidget.setSelectedDate(d)
        self.selectionChanged()

    def selectionChanged(self):
        self.date.setText(self.calendarWidget.selectedDate().toString('dd MMM yyyy'))

    def currentPageChanged(self, year,  month):
        months = (year - self.calendarWidget.selectedDate().year()) * 12 + month - self.calendarWidget.selectedDate().month()
        self.calendarWidget.setSelectedDate(self.calendarWidget.selectedDate().addMonths(months))

    def event(self, event):
        if event.type() == QtCore.QEvent.WindowDeactivate and not self.persistent: # стандартный попап меня пока не устраивает
            self.close() 
            return True # should return true if the event was recognized and processed
        return super().event(event)

    def positionPopup(self): # taken from QtCore.QDatetimeedit.cpp
        parent = self.parent()
        if not isinstance(parent, WDateEdit): return
        pos = parent.mapToGlobal(parent.rect().bottomLeft())
        screen = QtGui.QApplication.desktop().availableGeometry()

        y = pos.y()
        if y > screen.bottom() - self.height():
            y = parent.mapToGlobal(parent.rect().topLeft()).y() - self.height()
        
        pos.setX(max(screen.left(), min(screen.right() - self.width(), pos.x())))
        pos.setY(max(screen.top(), y))
        self.move(pos)
        
    def accepted(self):
        if self.persistent: return
        if isinstance(self.parent(), WDateEdit):
            qDate = self.calendarWidget.selectedDate()
            self.parent().setText(str(Date(qDate.year(), qDate.month(), qDate.day())))
            self.parent().applyCurrentValue(force=True)
        self.close()
    
    def keyPressEvent(self, event): # keyPress on form
        key = event.key()
        if event.modifiers() == QtCore.Qt.NoModifier:
            if key == QtCore.Qt.Key_Insert:
                if not self.persistent:
                    self.accepted()
                    return # pressing again Insert closes popup calendar
            elif key == QtCore.Qt.Key_Escape:
                if not self.persistent:
                    self.close()
                    return
        super().keyPressEvent(event)

    def eventFilter(self, target, event): # target - calendarWidget or any of its children
        if event.type() == QtCore.QEvent.KeyPress:
            key = event.key()
            if event.modifiers() == QtCore.Qt.NoModifier:
                if key == QtCore.Qt.Key_PageDown:
                    self.nextMonth.animateClick()
                    return True
                if key == QtCore.Qt.Key_PageUp:
                    self.prevMonth.animateClick()
                    return True
            elif event.modifiers() == QtCore.Qt.ControlModifier:
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
    
    def __init__(self, parent = None):
        super().__init__(parent)
        #self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        self.selector = QtGui.QToolButton(self)
        self.selector.setIcon(QtGui.QIcon(':/icons/fugue/calendar-blue.png'))
        self.selector.setCursor(QtCore.Qt.ArrowCursor)
        self.selector.setStyleSheet('QToolButton { border: none; padding: 0px; }')
        self.selector.setFocusPolicy(QtCore.Qt.NoFocus)

        self.selector.clicked.connect(self.showPopupCalendar)
        self.textChanged.connect(self.handleTextChanged)

        self.showSelector = True
        self.value = None

    def resizeEvent(self, event):
        sz = self.selector.sizeHint()
        frameWidth = self.style().pixelMetric(QtGui.QStyle.PM_DefaultFrameWidth)
        self.selector.move(self.rect().right() - frameWidth - sz.width(),
                      (self.rect().bottom() + 1 - sz.height()) / 2)
                      
    def handleTextChanged(self, txt):
        txt = list(str(txt))
        curPos = self.cursorPosition()
        i = 0
        while i < len(txt):
            char = txt[i]
            if not (char.isdigit() or char == ' '): 
                del txt[i]
                if i < curPos: curPos -= 1 # курсор должен находится все после той же цифры
            else: 
                i += 1
        len_ = 8 # standard length (__.__.____)
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
                self.showPopupCalendar()
                return
            elif key == QtCore.Qt.Key_Down:
                self.addDays(-1)
                return
            elif key == QtCore.Qt.Key_Up:
                self.addDays(1)
                return
            elif key in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):
                self.applyCurrentValue(force=True)
                return
            elif key == QtCore.Qt.Key_Left:
                if self.hasSelectedText():
                    self.setCursorPosition(self.selectionStart()) # переместим курсор на начало выделения - чтобы было удобнее
        super().keyPressEvent(keyEvent)

    def focusOutEvent(self, focusEvent):
        self.applyCurrentValue()
        super().focusOutEvent(focusEvent)
    
    def wheelEvent(self, wheelEvent):
        if not self.hasFocus(): return
        self.setCursorPosition(self.cursorPositionAt(wheelEvent.pos()))
        self.addDays(int(wheelEvent.delta() / 120))
        wheelEvent.ignore()

    def addDays(self, number): # target - lineEdit
        curPos = self.cursorPosition()
        d = Date(self.text())
        if not d: # empty or malformed date
            return
        if curPos <= 2: # day was 'wheeled'
            self.setText(str(d + number))
            self.setSelection(0, 2)
        elif curPos <= 5: # month was 'wheeled'
            self.setText(str(d.addMonths(number)))
            self.setSelection(3, 2)
        else: # year was 'wheeled'
            self.setText(str(d.addMonths(number*12)))
            self.setSelection(6, 4)
            
    def showPopupCalendar(self):
        self.selectAll()
        WCalendarPopup(self).show()

    def getShowSelector(self): return self.selector.isVisible()        
    def setShowSelector(self, value):
        self.selector.setVisible(value)
        borderWidth = self.style().pixelMetric(QtGui.QStyle.PM_DefaultFrameWidth) + 1
        paddingRight = borderWidth + (self.selector.sizeHint().width() if value else 0) 
        self.setStyleSheet('QLineEdit { padding-right: %dpx; }' % paddingRight)
        fm = QtGui.QFontMetrics(self.font()) # font metrics
        self.setMinimumSize(fm.width(str(Date.today())) + self.selector.sizeHint().height() + borderWidth * 2,
                max(fm.height(), self.selector.sizeHint().height() + borderWidth * 2))
    showSelector = QtCore.pyqtProperty(bool, getShowSelector, setShowSelector)

    def getValue(self): return self.__date
    def setValue(self, value):
        self.__date = Date(value)
        self.setText(str(self.__date))
        self.setCursorPosition(0)            
    value = QtCore.pyqtProperty(QtCore.QDate, getValue, setValue)
    
    #setMinimumDate
    #setMaximumDate

    def currentValue(self, currentText=''): #return introduced string as date
        if not currentText: currentText = self.text()
        return Date(currentText)

    def applyCurrentValue(self, force=False):
        currentValue = self.currentValue()
        if self.__date != currentValue or force:
            self.__date = currentValue
            self.edited.emit()
        if not currentValue:
            for char in self.text():
                if char.isdigit():
                    self.setStyleSheet('QLineEdit { background-color: yellow }')
                    return
        self.setStyleSheet('QLineEdit { background-color: white }')
            


if __name__ == '__main__': # some tests
    import sys
    app = QtGui.QApplication(sys.argv)
    m = WDateEdit(None)
    m.show()
    app.exec()
