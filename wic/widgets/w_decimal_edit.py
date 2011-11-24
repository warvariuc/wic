from PyQt4 import QtGui, QtCore
from wic.widgets import ui_w_popup_calculator
import re, decimal
Dec = decimal.Decimal


class WPopupCalculator(QtGui.QWidget, ui_w_popup_calculator.Ui_WPopupCalculator):
    '''Popup calculator'''
    
    operators = '+-*/' # static member
    
    keysBindings = {
        QtCore.Qt.Key_Enter: 'okButton', QtCore.Qt.Key_Return: 'okButton',
        QtCore.Qt.Key_Backspace: 'backspaceButton', QtCore.Qt.Key_Delete: 'clearButton',
        '=': 'equalButton', '0': 'digitButton_0', '1': 'digitButton_1', '2': 'digitButton_2', 
        '3': 'digitButton_3', '4': 'digitButton_4', '5': 'digitButton_5', '6': 'digitButton_6', 
        '7': 'digitButton_7', '8': 'digitButton_8', '9': 'digitButton_9', '+': 'plusButton',
        '-': 'minusButton', '*': 'multiplyButton', '/': 'divideButton', '.': 'pointButton', '%': 'percentButton'
    }

    def __init__(self, parent, persistent= False):
        if not parent: 
            persistent = True
        self.persistent = persistent
        windowStyle = QtCore.Qt.Tool if persistent else QtCore.Qt.Popup #Window | QtCore.Qt.CustomizeWindowHint
        super().__init__(parent, windowStyle)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose) # освобождать память - надо исследовать этот вопрос
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(':/icons/fugue/calculator-scientific.png'))
        
        if isinstance(parent, WDecimalEdit):
            parent.setFocus()
            self.value = parent.currentValue()
        else:
            self.value = Dec(0)
        
        self.positionPopup()
        self.okButton.setDisabled(persistent)
        self.display.setText(WDecimalEdit.regularNotation(self.value))

        bindings = {'0': self.digitButton_0, '1': self.digitButton_1,
                    '2': self.digitButton_2, '3': self.digitButton_3,
                    '4': self.digitButton_4, '5': self.digitButton_5,
                    '6': self.digitButton_6, '7': self.digitButton_7,
                    '8': self.digitButton_8, '9': self.digitButton_9,
                    '.': self.pointButton, '+/-': self.changeSignButton,
                    'b': self.backspaceButton, 'c': self.clearButton,
                    '/': self.divideButton, '*': self.multiplyButton,
                    '-': self.minusButton, '+': self.plusButton,
                    '=': self.equalButton, 'sqrt': self.squareRootButton,
                    'x**2': self.powerButton, '1/x': self.reciprocalButton,
                    '%': self.percentButton}
        def bind(button, code):
            button.clicked.connect(lambda: self.on_buttonClicked(code))
        for code, button in bindings.items():
            bind(button, code)
            
 
    def on_buttonClicked(self, code):
        expr = str(self.display.text())
        if expr == 'NaN': 
            expr = '0'
        if code == 'b': # backspace
            self.display.setText(expr[:-1]  if len(expr) != 1 else '0')
        elif code == 'c': # clear
            self.calculateResult('')
        elif code == '+/-':
            self.calculateResult('-(%s)' % expr)
        elif code == 'sqrt':
            self.calculateResult('(%s).sqrt()' % expr)
        elif code == 'x**2':
            self.calculateResult('(%s)**2' % expr)
        elif code == '.':
            if expr[-1:] != '%':
                parts = re.split('([' + re.escape(self.operators) + '])', expr)
                if '.' not in parts[-1]: #проверим, если последнее введенное число уже содержит точку
                    self.display.setText(expr + '.')
        elif code == '1/x':
            self.calculateResult('1/(%s)' % expr)
        elif code == '=':
            self.calculateResult(expr)
        elif code in self.operators: 
            if expr [-1:] in self.operators + '.':
                self.display.setText(expr [:-1] + code) # overwrite last operator
            else:
                self.display.setText(expr + code)
        elif code == '%':
            parts = re.split('([' + re.escape(self.operators) + '])', expr)
            if code not in parts[-1] and parts[-1] not in self.operators:
                self.display.setText(expr + code)
        elif code.isdigit():
            if expr == '0': #replace leading 0                
                self.display.setText(code)
            elif expr[-1:] != '%':
                self.display.setText(expr + code)

    def calculateResult(self, expr):
        if not expr:
            result = Dec('0')
        else:
            if expr[-1:] in self.operators + '.':
                expr = expr[:-1] # обрезаем оператор в конце строки, когда после него не был введен операнд
            expr = re.sub(r'(\d*\.?\d+)', r'Dec(str("\1"))', expr)
            expr = re.sub(r'%', r'*Dec("0.01")', expr) # можно было и поделить на 100, но, мне кажется, умножение быстрее
            result = eval(expr)
        self.display.setText(WDecimalEdit.regularNotation(result))

    @QtCore.pyqtSlot()
    def on_okButton_clicked(self):
        self.calculateResult(str(self.display.text()))
        self.parent().setValue(self.display.text(), emitEdited= True) 
        self.close()
        
    def keyPressEvent(self, keyEvent):
        buttonName = None
        if keyEvent.modifiers() in (QtCore.Qt.NoModifier, QtCore.Qt.KeypadModifier):
            key = keyEvent.key()
            if key in (QtCore.Qt.Key_Escape, QtCore.Qt.Key_Insert):
                if not self.persistent:
                    self.close()
                    return
            buttonName = self.keysBindings.get(key) # check a non-text pressed key
        if not buttonName: # check a text pressed key
            buttonName = self.keysBindings.get(keyEvent.text())
        if buttonName:
            getattr(self, buttonName).animateClick() # call the slot
        else:
            super().keyPressEvent(keyEvent) 

    def positionPopup(self): # taken from qdatetimeedit.cpp
        parent = self.parent()
        if isinstance(parent, WDecimalEdit): 
            pos = parent.mapToGlobal(parent.rect().bottomRight())
            screen = QtGui.QApplication.desktop().availableGeometry()
    
            y = pos.y()
            if y > screen.bottom() - self.height():
                y = parent.mapToGlobal(parent.rect().topLeft()).y() - self.height()
            
            pos.setX(max(screen.left(), min(screen.right() - self.width(), pos.x() - self.width())))
            pos.setY(max(screen.top(), y))
            self.move(pos)
        



class WDecimalEdit(QtGui.QLineEdit):
    'Custom widget - for editing decimals. You can specify total number of digits, fractional part digits.'
    
    edited = QtCore.pyqtSignal()
    
    def __init__(self, parent= None):
        super().__init__(parent)
        #self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setAlignment(QtCore.Qt.AlignRight)
        self.selector = QtGui.QToolButton(self)
        self.selector.setIcon(QtGui.QIcon(':/icons/calculator.png'))
        self.selector.setCursor(QtCore.Qt.PointingHandCursor)
        self.selector.setStyleSheet('QToolButton { border: none; padding: 0px; }')
        self.selector.setFocusPolicy(QtCore.Qt.NoFocus)
        
        self.selector.clicked.connect(self.popupCalculator)
        self.textChanged.connect(self.onTextChanged)
        
        self.menu = QtGui.QMenu(self) # context menu
        self.menu.addAction(QtGui.QIcon(':/icons/fugue/calculator-scientific.png'), 'Calculator', self.popupCalculator, QtGui.QKeySequence(QtCore.Qt.Key_Insert))
        self.menu.addAction(QtGui.QIcon(':/icons/fugue/document-copy.png'), 'Copy', self.copy, QtGui.QKeySequence(QtGui.QKeySequence.Copy))
        self.menu.addAction(QtGui.QIcon(':/icons/fugue/clipboard-paste.png'), 'Paste', self.paste, QtGui.QKeySequence(QtGui.QKeySequence.Paste))
        self.menu.addAction(QtGui.QIcon(':/icons/fugue/eraser.png'), 'Clear', self.clear)

        self.setSelectorVisible(True) # cause style recalculation
        self._totalDigits = 15 # total number of digits
        self._fractionDigits = 2 # number of digits in fractional part
        self._nonNegative = False
        self._separateThousands = True
        self._isHandlingTextChanged = False
        self.value = '0' # will cause text update

    def getMaxDigits(self): 
        return self._totalDigits
    def setMaxDigits(self, value):
        assert isinstance(value, int), 'Pass an integer'
        self._totalDigits = max(value, 1)
        self._fractionDigits = min(self._fractionDigits, self._totalDigits)
        self.onTextChanged(self.text()) # to reflect changes
    maxDigits = QtCore.pyqtProperty(int, getMaxDigits, setMaxDigits) 

    def getFractionDigits(self): 
        return self._fractionDigits
    def setFractionDigits(self, value):
        self._fractionDigits = max(value, -1)
        self._totalDigits = max(self._totalDigits, self._fractionDigits)
        self.onTextChanged(self.text())
    fractionDigits = QtCore.pyqtProperty(int, getFractionDigits, setFractionDigits)

    def isNonNegative(self): 
        return self._nonNegative
    def setSetNonegative(self, value): 
        self._nonNegative = bool(value)
        self.onTextChanged(self.text())
    nonNegative = QtCore.pyqtProperty(bool, isNonNegative, setSetNonegative)
    
    def isThousandsSeparated(self): 
        return self._separateThousands
    def setThousandsSeparated(self, value): 
        self._separateThousands = bool(value)
        self.onTextChanged(self.text())
    thousandsSeparated = QtCore.pyqtProperty(bool, isThousandsSeparated, setThousandsSeparated)

    def getValue(self): 
        return self._value
    def setValue(self, value, emitEdited= False):
        value = Dec(str(value))
        if self._fractionDigits != -1:
            value = round(value, self._fractionDigits)
        self.setText(self.regularNotation(value))
        self.setCursorPosition(0)
        self._value = self.currentValue()
        if emitEdited:
            self.edited.emit()
    value = QtCore.pyqtProperty(float, getValue, setValue)
    
    def resizeEvent(self, event):
        sz = self.selector.sizeHint()
        frameWidth = self.style().pixelMetric(QtGui.QStyle.PM_DefaultFrameWidth)
        self.selector.move(self.rect().right() - frameWidth - sz.width(),
                      (self.rect().bottom() + 1 - sz.height()) / 2)
    
    def isSelectorVisible(self): 
        return not self.selector.isHidden()
    def setSelectorVisible(self, value):
        self.selector.setVisible(value)
        borderWidth = self.style().pixelMetric(QtGui.QStyle.PM_DefaultFrameWidth) + 1
        paddingRight = borderWidth + (self.selector.sizeHint().width() if value else 0) 
        self.setStyleSheet('QLineEdit { padding-right: %dpx; }' % paddingRight)
        fm = QtGui.QFontMetrics(self.font()) # font metrics
        self.setMinimumSize(fm.width(str('0.00')) + self.selector.sizeHint().height() + borderWidth * 2,
                   max(fm.height(), self.selector.sizeHint().height() + borderWidth * 2))
    selectorVisible = QtCore.pyqtProperty(bool, isSelectorVisible, setSelectorVisible)

    def mouseDoubleClickEvent(self, mouseEvent):
        if mouseEvent.button() == QtCore.Qt.LeftButton:
            self.selectAll() # select all on double click, otherwise only group of digits will be selected
            
    def keyPressEvent(self, keyEvent):
        key = keyEvent.key()
        if keyEvent.modifiers() in (QtCore.Qt.NoModifier, QtCore.Qt.KeypadModifier):
            if key == QtCore.Qt.Key_Insert:
                self.popupCalculator()
                return
            elif key in (QtCore.Qt.Key_Backspace, QtCore.Qt.Key_Delete) and not self.hasSelectedText():
                txt = self.text()
                curPos = self.cursorPosition()
                if key == QtCore.Qt.Key_Backspace:
                    posDel = curPos - 1 # position to check for character
                    posMove = curPos - 1 # position to move to
                elif key == QtCore.Qt.Key_Delete:
                    posDel = curPos
                    posMove = curPos + 1
                if 0 <= posDel < len(txt):
                    charDel = txt[posDel] 
                    if (charDel == '.' and self._fractionDigits > 0) or charDel == ',': # the char to be deleted is a dot or thousands separator
                        self.setCursorPosition(posMove) # jump over the char
            elif key in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):
                self.applyCurrentValue(force= True)
                return
        if self.cursorPosition() == 0:
            if self.text().startswith('0'):
                if keyEvent.text().isdigit() or keyEvent.text() == '.':
                    self.setCursorPosition(1)
        super().keyPressEvent(keyEvent)

    def focusOutEvent(self, focusEvent):
        'Check for changes when leaving the widget'
        if focusEvent.reason() != QtCore.Qt.PopupFocusReason: # контекстное меню выскочило или еще что
            self.applyCurrentValue()
        super().focusOutEvent(focusEvent)
        
    def onTextChanged(self, txt):
        if self._isHandlingTextChanged: return
        self._isHandlingTextChanged = True
        if self._fractionDigits > 0: 
            txt += '.' + '0' * self._fractionDigits
        txt = list(txt)
        curPos = self.cursorPosition()
        dotPos = -1
        i = 0
        negative = False
        while i < len(txt):
            char = txt[i]
            del_ = False # delete current symbol
            if char == '-': 
                negative = not negative
                del_ = True
            elif (i == 0) and (char == '0'): 
                del_ = True # leading zero
            elif char == '.':
                if dotPos == -1: # найдена первая точка и предполагается дробная часть
                    dotPos = i
                    if not self._fractionDigits:
                        del txt[i:] # удалить оставшуся часть - там ничего важного - точка найдена, а дробной части нет
                        break
                else: 
                    if self._fractionDigits == -1: # вторая точка, а длина дробной части не фиксированна
                        del txt[i:] # удалить оставшуюся часть
                        break
                    del_ = True # found next dot
            elif not char.isdigit(): #минус и точку проверили, все остальные не-цифры удаляем
                del_ = True # non-digit
            elif dotPos == -1: # это цифра. точка еще не была
                if i >= self._totalDigits - max(self._fractionDigits, 0): #  отсекаем лишние цифры целой части
                    del_ = True
            else: # это цифра. точка уже была найдена
                if i - dotPos > self._fractionDigits >= 0 :#or not self._fractionDigits: # отсекаем лишние цифры дробной части
                    del_ = True # digits number before dot limit reached
            
            if del_: # delete current symbol
                del txt[i]
                if i < curPos: 
                    curPos -= 1
            else: 
                i += 1
            
        i = dotPos if dotPos != -1 else len(txt)
        while self._separateThousands:
            i -= 3
            if i <= 0: break
            txt.insert(i, ',')
            if i < curPos: 
                curPos += 1
        if not txt:
            txt = '0'
            if curPos: curPos = 1
        if negative and not self.nonNegative:# and self.currentValue(txt) != Dec(0):
            txt.insert(0, '-')
            curPos += 1
        self.setText(''.join(txt))
        self.setCursorPosition(curPos)
        self._isHandlingTextChanged = False

    def currentValue(self, currentText= None): #return introduced string as decimal
        return Dec(((currentText if currentText is not None else self.text())).replace(',', ''))

    def applyCurrentValue(self, force= False):
        currentValue = self.currentValue()
        self.setText(self.regularNotation(currentValue))
        if self._value != currentValue or force:
            self.setValue(currentValue, emitEdited= True)

    def popupCalculator(self):
        self.selectAll()
        WPopupCalculator(self).show()
        
    def valueStr(self):
        return self.regularNotation(self.value)

    @staticmethod
    def regularNotation(value):
        v = '{:.14f}'.format(value).rpartition('.') # 14 цифр после запятой
        return v if not v[1] else v[0] + (v[1] + v[2]).rstrip('.0') # убираем последние нули в дробной части
        
    def contextMenuEvent(self, qContextMenuEvent):
        self.selectAll()
        self.menu.popup(qContextMenuEvent.globalPos())


if __name__ == '__main__': # some tests
    app = QtGui.QApplication([])
    #m = WPopupCalculator(None, True)
    widget = WDecimalEdit(None)
    widget.show()
    app.exec()
