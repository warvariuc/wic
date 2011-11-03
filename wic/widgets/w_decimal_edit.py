from PyQt4 import QtGui, QtCore
from wic.widgets import ui_w_popup_calculator
import re, decimal
Dec = decimal.Decimal

class WPopupCalculator(QtGui.QWidget, ui_w_popup_calculator.Ui_WPopupCalculator):
    '''Popup calculator'''
    
    operators = '+-*/' # static member
    
    keysBindings = {
        QtCore.Qt.Key_Insert: 'okButton', QtCore.Qt.Key_Enter: 'okButton', QtCore.Qt.Key_Return: 'okButton',
        QtCore.Qt.Key_Backspace: 'backspaceButton', QtCore.Qt.Key_Delete: 'clearButton',
        '=': 'equalButton', '0': 'digitButton_0', '1': 'digitButton_1', '2': 'digitButton_2', 
        '3': 'digitButton_3', '4': 'digitButton_4', '5': 'digitButton_5', '6': 'digitButton_6', 
        '7': 'digitButton_7', '8': 'digitButton_8', '9': 'digitButton_9', '+': 'plusButton',
        '-': 'minusButton', '*': 'multiplyButton', '/': 'divideButton', '.': 'pointButton', '%': 'percentButton'
    }

    def __init__(self, parent, persistent= False):
        if not parent: persistent = True
        windowStyle = QtCore.Qt.Tool if persistent else QtCore.Qt.Popup #Window | QtCore.Qt.CustomizeWindowHint
        super().__init__(parent, windowStyle) # стандартный попап меня пока не устраивает - он модальный
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose) # освобождать память - надо исследовать этот вопрос
        self.setupUi(self)
        if isinstance(parent, WDecimalEdit):
            parent.setFocus()
            self.value = parent.currentValue()
        else:
            self.value = Dec(0)
        
        self.positionPopup()
        self.persistent = persistent
        self.okButton.setDisabled(persistent)
        self.display.setText(WDecimalEdit.regularNotation(self.value))

        def bind(button, code):
            button.clicked.connect(lambda: self.buttonClicked(code))

        bind(self.digitButton_0, '0'); bind(self.digitButton_1, '1')
        bind(self.digitButton_2, '2'); bind(self.digitButton_3, '3')
        bind(self.digitButton_4, '4'); bind(self.digitButton_5, '5')
        bind(self.digitButton_6, '6'); bind(self.digitButton_7, '7')
        bind(self.digitButton_8, '8'); bind(self.digitButton_9, '9')
        bind(self.pointButton, '.'); bind(self.changeSignButton, '+/-')
        bind(self.backspaceButton, 'b'); bind(self.clearButton, 'c')
        bind(self.divideButton, '/'); bind(self.multiplyButton, '*')
        bind(self.minusButton, '-'); bind(self.plusButton, '+')
        bind(self.equalButton, '='); bind(self.squareRootButton, 'sqrt')
        bind(self.powerButton, 'x**2'); bind(self.reciprocalButton, '1/x')
        bind(self.percentButton, '%')
        self.okButton.clicked.connect(self.okButtonClicked)
 
    def buttonClicked(self, code):
        expr = str(self.display.text())
        if expr == 'NaN': expr = '0'
        if code == 'b': # backspace
            self.display.setText(expr[:-1]  if len(expr) != 1 else '0')
        elif code == 'c': # clear
            self.calculateResult('')
        elif code == '+/-':
            self.calculateResult('-(' + expr + ')')
        elif code == 'sqrt':
            self.calculateResult('(' + expr + ').sqrt()')
        elif code == 'x**2':
            self.calculateResult('(' + expr + ')**2')
        elif code == '.':
            if expr[-1:] != '%':
                parts = re.split('([' + re.escape(self.operators) + '])', expr)
                if '.' not in parts[-1]: #проверим, если последнее введенное число уже содержит точку
                    self.display.setText(expr + '.')
        elif code == '1/x':
            self.calculateResult('1/(' + expr + ')')
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

    def okButtonClicked(self):
        self.calculateResult(str(self.display.text()))
        self.parent().value = self.display.text()
        self.parent().applyCurrentValue(force=True)
        self.close()
        
    def keyPressEvent(self, keyEvent):
        buttonName = ''
        if keyEvent.modifiers() in (QtCore.Qt.NoModifier, QtCore.Qt.KeypadModifier):
            key = keyEvent.key()
            if key in (QtCore.Qt.Key_Escape, QtCore.Qt.Key_End):
                if not self.persistent:
                    self.close()
                    return
            try: buttonName = self.keysBindings[key] #check a non-text pressed key
            except: pass
        if not buttonName: #check a text pressed key
            try: buttonName = self.keysBindings[keyEvent.text()] 
            except: pass
        if buttonName:
            getattr(self, buttonName).animateClick() #call the method
            return
        
        super().keyPressEvent(keyEvent) 

    def event(self, event):
        if event.type() == QtCore.QEvent.WindowDeactivate and not self.persistent: # стандартный попап меня пока не устраивает - 'слишком' модальный
            self.close() 
        return super().event(event)
        
    def positionPopup(self): # taken from qdatetimeedit.cpp
        parent = self.parent()
        if not isinstance(parent, WDecimalEdit): return
        pos = parent.mapToGlobal(parent.rect().bottomLeft())
        screen = QtGui.QApplication.desktop().availableGeometry()

        y = pos.y()
        if y > screen.bottom() - self.height():
            y = parent.mapToGlobal(parent.rect().topLeft()).y() - self.height()
        
        pos.setX(max(screen.left(), min(screen.right() - self.width(), pos.x())))
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
        self.selector.setCursor(QtCore.Qt.ArrowCursor)
        self.selector.setStyleSheet('QToolButton { border: none; padding: 0px; }')
        self.selector.setFocusPolicy(QtCore.Qt.NoFocus)
        self.selector.clicked.connect(self.popupCalculator)
        self.textChanged.connect(self.handleTextChanged)
        
        self.menu = QtGui.QMenu(self) # context menu
        self.menu.addAction(QtGui.QIcon(':/icons/calculator.png'), 'Калькулятор', self.popupCalculator, QtGui.QKeySequence(QtCore.Qt.Key_Insert))
        self.menu.addAction(QtGui.QIcon(':/icons/fugue/document-copy.png'), 'Копировать', self.copy, QtGui.QKeySequence(QtGui.QKeySequence.Copy))
        self.menu.addAction(QtGui.QIcon(':/icons/fugue/clipboard-paste.png'), 'Вставить', self.paste, QtGui.QKeySequence(QtGui.QKeySequence.Paste))
        self.menu.addAction(QtGui.QIcon(':/icons/fugue/eraser.png'), 'Очистить', self.clear)

        self.showSelector = True
        self.__totalDigits = 15 # total number of digits
        self.__fractionDigits = 2 # number of digits in fractional part
        self.__nonNegative = False
        self.__separateThousands = True
        self.__isHandlingTextChanged = False
        self.value = '0' # will cause text update

    def getTotalDigits(self): return self.__totalDigits
    def setTotalDigits(self, value): 
        self.__totalDigits = max(value, 1)
        self.__fractionDigits = min(self.__fractionDigits, self.__totalDigits)
        self.handleTextChanged(self.text()) #to reflect changes
    totalDigits = QtCore.pyqtProperty(int, getTotalDigits, setTotalDigits) 

    def getFractionDigits(self): return self.__fractionDigits
    def setFractionDigits(self, value):
        self.__fractionDigits = max(value, -1)
        self.__totalDigits = max(self.__totalDigits, self.__fractionDigits)
        self.handleTextChanged(self.text())
    fractionDigits = QtCore.pyqtProperty(int, getFractionDigits, setFractionDigits)

    def getShowSelector(self): return self.selector.isVisible()
    def setShowSelector(self, value):
        self.selector.setVisible(value)
        borderWidth = self.style().pixelMetric(QtGui.QStyle.PM_DefaultFrameWidth) + 1
        paddingRight = borderWidth + (self.selector.sizeHint().width() if value else 0) 
        self.setStyleSheet('QLineEdit { padding-right: %dpx; }' % paddingRight)
        fm = QtGui.QFontMetrics(self.font()) # font metrics
        self.setMinimumSize(fm.width(str('0.00')) + self.selector.sizeHint().height() + borderWidth * 2,
                   max(fm.height(), self.selector.sizeHint().height() + borderWidth * 2))
    showSelector = QtCore.pyqtProperty(bool, getShowSelector, setShowSelector)

    def getNonNegative(self): return self.__nonNegative
    def setSetNonegative(self, value): 
        self.__nonNegative = bool(value)
        self.handleTextChanged(self.text())
    nonNegative = QtCore.pyqtProperty(bool, getNonNegative, setSetNonegative)
    
    def getSeparateThousands(self): return self.__separateThousands
    def setSeparateThousands(self, value): 
        self.__separateThousands = bool(value)
        self.handleTextChanged(self.text())
    separateThousands = QtCore.pyqtProperty(bool, getSeparateThousands, setSeparateThousands)

    def getValue(self): return self.__value
    def setValue(self, value):
        value = Dec(str(value))
        if self.__fractionDigits != -1:
            value = round(value, self.__fractionDigits)
        self.setText(self.regularNotation(value))
        self.setCursorPosition(0)
        self.__value = self.currentValue()
    value = QtCore.pyqtProperty(float, getValue, setValue)
    
    def resizeEvent(self, event):
        sz = self.selector.sizeHint()
        frameWidth = self.style().pixelMetric(QtGui.QStyle.PM_DefaultFrameWidth)
        self.selector.move(self.rect().right() - frameWidth - sz.width(),
                      (self.rect().bottom() + 1 - sz.height()) / 2)
    
    def mouseDoubleClickEvent(self, mouseEvent):
        if mouseEvent.button() == QtCore.Qt.LeftButton:
            self.selectAll() # select all on double click, otherwise only group of digits will be selected
            
    def keyPressEvent(self, keyEvent):
        key = keyEvent.key()
        if keyEvent.modifiers() == QtCore.Qt.NoModifier:
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
                    if (charDel == '.' and self.__fractionDigits > 0) or charDel == ',': # the char to be deleted is a dot or thousands separator
                        self.setCursorPosition(posMove) # jump over the char
        
        if keyEvent.modifiers() in (QtCore.Qt.NoModifier, QtCore.Qt.KeypadModifier):
            if key in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):
                self.applyCurrentValue(force=True)
            if self.cursorPosition() == 0:
                if self.text().startswith('0'):
                    if keyEvent.text().isdigit() or keyEvent.text() == '.':
                        self.setCursorPosition(1)
        super().keyPressEvent(keyEvent)

#    def focusInEvent(self, focusEvent):
#        super().focusInEvent(focusEvent)
#        QtCore.QTimer.singleShot(0, self.selectAll)
#        #self.selectAll()
        
    def focusOutEvent(self, focusEvent):
        'Check for changes when leaving the widget'
        if focusEvent.reason() != QtCore.Qt.PopupFocusReason: # контекстное меню выскочило или еще что
            self.applyCurrentValue()
        super().focusOutEvent(focusEvent)
        
    def handleTextChanged(self, txt):
        if self.__isHandlingTextChanged: return
        self.__isHandlingTextChanged = True
        if self.__fractionDigits > 0: txt += '.' + '0' * self.__fractionDigits
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
                    if not self.__fractionDigits:
                        del txt[i:] # удалить оставшуся часть - там ничего важного - точка найдена, а дробной части нет
                        break
                else: 
                    if self.__fractionDigits == -1: # вторая точка, а длина дробной части не фиксированна
                        del txt[i:] # удалить оставшуюся часть
                        break
                    del_ = True # found next dot
            elif not char.isdigit(): #минус и точку проверили, все остальные не-цифры удаляем
                del_ = True # non-digit
            elif dotPos == -1: # это цифра. точка еще не была
                if i >= self.__totalDigits - max(self.__fractionDigits, 0): #  отсекаем лишние цифры целой части
                    del_ = True
            else: # это цифра. точка уже была найдена
                if i - dotPos > self.__fractionDigits >= 0 :#or not self.__fractionDigits: # отсекаем лишние цифры дробной части
                    del_ = True # digits number before dot limit reached
            
            if del_: # delete current symbol
                del txt[i]
                if i < curPos: 
                    curPos -= 1
            else: 
                i += 1
            
        i = dotPos if dotPos != -1 else len(txt)
        while self.__separateThousands:
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
#            self.setStyleSheet("color: red"); # show negative number in red
#        else:
#            self.setStyleSheet("color: black");
        self.setText(''.join(txt))
        self.setCursorPosition(curPos)
        self.__isHandlingTextChanged = False

    def currentValue(self, currentText= None): #return introduced string as decimal
        return Dec(((currentText if currentText is not None else self.text())).replace(',', ''))

    def applyCurrentValue(self, force= False):
        currentValue = self.currentValue()
        self.setText(self.regularNotation(currentValue))
        if self.__value != currentValue or force:
            self.__value = currentValue
            self.edited.emit()

    def popupCalculator(self):
        self.selectAll()
        WPopupCalculator(self).show()
        
    def valueStr(self):
        return self.regularNotation(self.value)

    @staticmethod
    def regularNotation(d):
        d = '{:.14f}'.format(d).rpartition('.') # 14 цифр после запятой
        return d if not d[1] else d[0] + (d[1] + d[2]).rstrip('.0') # убираем последние нули в дробной части
        
    def contextMenuEvent(self, qContextMenuEvent):
        self.selectAll()
        self.menu.popup(qContextMenuEvent.globalPos())


if __name__ == '__main__': # some tests
    app = QtGui.QApplication([])
    #m = WPopupCalculator(None, True)
    widget = WDecimalEdit(None)
    widget.show()
    app.exec()
