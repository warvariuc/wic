import re
from decimal import Decimal

from PyQt5 import QtGui, QtCore, QtWidgets

from . import ui_popup_calculator


def regular_notation(value):
    """Sometimes str(decimal) makes scientific notation. This function makes the regular notation.
    """
    # 14 digits after the dot
    v = '{:.14f}'.format(value).rpartition('.')
    # remove trailing zerios in the fractional part
    return v[0] + (v[1] + v[2]).rstrip('.0')


class PopupCalculator(QtWidgets.QWidget, ui_popup_calculator.Ui_PopupCalculator):
    """Calculator window.
    """
    operators = '+-*/'
    
    keysBindings = {
        QtCore.Qt.Key_Enter: 'okButton',
        QtCore.Qt.Key_Return: 'okButton',
        QtCore.Qt.Key_Backspace: 'backspaceButton',
        QtCore.Qt.Key_Delete: 'clearButton',
        '=': 'equalButton',
        '0': 'digitButton_0',
        '1': 'digitButton_1',
        '2': 'digitButton_2',
        '3': 'digitButton_3',
        '4': 'digitButton_4',
        '5': 'digitButton_5',
        '6': 'digitButton_6',
        '7': 'digitButton_7',
        '8': 'digitButton_8',
        '9': 'digitButton_9',
        '+': 'plusButton',
        '-': 'minusButton',
        '*': 'multiplyButton',
        '/': 'divideButton',
        '.': 'pointButton',
        '%': 'percentButton',
    }

    def __init__(self, parent, persistent= False):
        if not parent: 
            persistent = True
        self.persistent = persistent
        windowStyle = QtCore.Qt.Tool if persistent else QtCore.Qt.Popup #Window | QtCore.Qt.CustomizeWindowHint

        super().__init__(parent, windowStyle)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(':/icons/fugue/calculator-scientific.png'))
        
        if isinstance(parent, DecimalEdit):
            parent.setFocus()
            self.value = parent.value()
        else:
            self.value = Decimal(0)
        
        self.positionPopup()
        self.okButton.setDisabled(persistent)
        self.display.setText(regular_notation(self.value))
        self._replace = True # whether next entered number should replace the one shown

        bindings = {
            '0': self.digitButton_0,
            '1': self.digitButton_1,
            '2': self.digitButton_2,
            '3': self.digitButton_3,
            '4': self.digitButton_4,
            '5': self.digitButton_5,
            '6': self.digitButton_6,
            '7': self.digitButton_7,
            '8': self.digitButton_8,
            '9': self.digitButton_9,
            '.': self.pointButton,
            '+/-': self.changeSignButton,
            'b': self.backspaceButton,
            'c': self.clearButton,
            '/': self.divideButton,
            '*': self.multiplyButton,
            '-': self.minusButton,
            '+': self.plusButton,
            '=': self.equalButton,
            'sqrt': self.squareRootButton,
            'x**2': self.powerButton,
            '1/x': self.reciprocalButton,
            '%': self.percentButton,
        }

        for code, button in bindings.items():
            button.clicked.connect(lambda state, code=code: self.on_buttonClicked(code))

    def on_buttonClicked(self, code):
        expr = self.display.text()
        if expr == 'NaN': 
            expr = '0'
        if code == 'b':  # backspace
            self.display.setText(expr[:-1]  if len(expr) != 1 else '0')
        elif code == 'c':  # clear
            self.calculateResult('0')
        elif code == '+/-':
            self.calculateResult('-(%s)' % expr)
        elif code == 'sqrt':
            self.calculateResult('(%s).sqrt()' % expr)
        elif code == 'x**2':
            self.calculateResult('(%s)**2' % expr)
        elif code == '1/x':
            self.calculateResult('1/(%s)' % expr)
        elif code == '=':
            self.calculateResult(expr)
            self._replace = True
            return
        elif code in self.operators: 
            if expr [-1:] in self.operators + '.':
                # overwrite last operator
                self.display.setText(expr [:-1] + code)
            else:
                self.display.setText(expr + code)
        elif code == '%':
            parts = re.split('([' + re.escape(self.operators) + '])', expr)
            if code not in parts[-1] and parts[-1] not in self.operators:
                self.display.setText(expr + code)
        else:
            if self._replace:
                expr = '0'
            if code == '.':
                if expr[-1:] != '%':
                    parts = re.split('([' + re.escape(self.operators) + '])', expr)
                    # if the last entered number already contains `.`
                    if '.' not in parts[-1]:
                        self.display.setText(expr + '.')
            elif code.isdigit():
                # replace leading 0
                if expr == '0':
                    self.display.setText(code)
                elif expr[-1:] != '%':
                    self.display.setText(expr + code)
        self._replace = False 

    def calculateResult(self, expr):
        if expr == 'NaN':
            result = Decimal()
        else:
            if expr[-1:] in self.operators + '.':
                # chop the last operator if no operand is after it
                expr = expr[:-1]
            expr = re.sub(r'(\d*\.?\d+)', r'Decimal(str("\1"))', expr)
            expr = re.sub(r'%', r'/Decimal(100)', expr)
            try:
                result = eval(expr)
            except Exception as exc:
                self.display.setText('NaN')
                print(exc)
                return
        self.display.setText(regular_notation(result))

    @QtCore.pyqtSlot()
    def on_okButton_clicked(self):
        self.calculateResult(str(self.display.text()))
        self.parent().setValue(self.display.text(), emit= True) 
        self.close()
        
    def keyPressEvent(self, keyEvent):
        buttonName = None
        if keyEvent.modifiers() in (QtCore.Qt.NoModifier, QtCore.Qt.KeypadModifier):
            key = keyEvent.key()
            if key in (QtCore.Qt.Key_Escape, QtCore.Qt.Key_Insert):
                if not self.persistent:
                    self.close()
                    return
            # check a non-text pressed key
            buttonName = self.keysBindings.get(key)
        # check a text pressed key
        buttonName = buttonName or self.keysBindings.get(keyEvent.text())
        if buttonName:
            # call the slot
            getattr(self, buttonName).animateClick()
        else:
            super().keyPressEvent(keyEvent) 

    def positionPopup(self):
        # from qdatetimeedit.cpp
        parent = self.parent()
        if isinstance(parent, DecimalEdit):
            pos = parent.mapToGlobal(parent.rect().bottomRight())
            screen = QtWidgets.QApplication.desktop().availableGeometry()
    
            y = pos.y()
            if y > screen.bottom() - self.height():
                y = parent.mapToGlobal(parent.rect().topLeft()).y() - self.height()
            
            pos.setX(max(screen.left(), min(screen.right() - self.width(), pos.x() - self.width())))
            pos.setY(max(screen.top(), y))
            self.move(pos)


class DecimalEdit(QtWidgets.QLineEdit):
    """
    Custom widget - for editing decimals. You can specify total number of digits,
    fractional part digits.
    """
    edited = QtCore.pyqtSignal()
    
    def __init__(self, parent= None):
        super().__init__(parent)
        #self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setAlignment(QtCore.Qt.AlignRight)
        self.selector = QtWidgets.QToolButton(self)
        self.selector.setIcon(QtGui.QIcon(':/icons/calculator.png'))
        self.selector.setCursor(QtCore.Qt.PointingHandCursor)
        self.selector.setStyleSheet('QToolButton { border: none; padding: 0px; }')
        self.selector.setFocusPolicy(QtCore.Qt.NoFocus)
        
        self.selector.clicked.connect(self.popupCalculator)
        self.textEdited.connect(self.onTextEdited)

        # context menu
        self.menu = QtWidgets.QMenu(self)
        self.menu.addAction(
            QtGui.QIcon(':/icons/fugue/calculator-scientific.png'), 'Calculator',
            self.popupCalculator, QtGui.QKeySequence(QtCore.Qt.Key_Insert))
        self.menu.addAction(
            QtGui.QIcon(':/icons/fugue/document-copy.png'), 'Copy',
            self.copy, QtGui.QKeySequence(QtGui.QKeySequence.Copy))
        self.menu.addAction(
            QtGui.QIcon(':/icons/fugue/clipboard-paste.png'), 'Paste',
            self.paste, QtGui.QKeySequence(QtGui.QKeySequence.Paste))
        self.menu.addAction(
            QtGui.QIcon(':/icons/fugue/eraser.png'), 'Clear',
            self.interactiveClear)

        # total number of digits
        self._maxDigits = 15
        # number of digits in fractional part. Initial value is -1 - to avoid chopping the text
        # when setFactionDigits is called after setText by uic
        self._fractionDigits = -1
        self._nonNegative = False
        self._separateThousands = True
        self.selectorVisible = True  # cause style recalculation
        self._newText = None  # is used to track editing
        self.setValue(0)  # call text update

    def maxDigits(self): 
        return self._maxDigits

    def setMaxDigits(self, value):
        assert isinstance(value, int), 'Pass an integer'
        self._maxDigits = max(value, 1)
        self._fractionDigits = min(self._fractionDigits, self._maxDigits)
        self._format()  # to reflect changes

    maxDigits = QtCore.pyqtProperty(int, maxDigits, setMaxDigits) 

    def fractionDigits(self): 
        return self._fractionDigits

    def setFractionDigits(self, value):
        """How many digits after decimal point to show. If is 0 - no fraction digits - an integer.
        If -1 - any number of digits in fractional part.
        """
        self._fractionDigits = max(value, -1)
        self._maxDigits = max(self._maxDigits, self._fractionDigits)
        self._format()

    fractionDigits = QtCore.pyqtProperty(int, fractionDigits, setFractionDigits)

    def isNonNegative(self): 
        return self._nonNegative

    def setSetNonegative(self, value): 
        self._nonNegative = bool(value)
        self._format()

    nonNegative = QtCore.pyqtProperty(bool, isNonNegative, setSetNonegative)
    
    def isThousandsSeparated(self): 
        return self._separateThousands
    def setThousandsSeparated(self, value): 
        self._separateThousands = bool(value)
        self._format()
    thousandsSeparated = QtCore.pyqtProperty(bool, isThousandsSeparated, setThousandsSeparated)

    def resizeEvent(self, event):
        sz = self.selector.sizeHint()
        frameWidth = self.style().pixelMetric(QtWidgets.QStyle.PM_DefaultFrameWidth)
        self.selector.move(
            self.rect().right() - frameWidth - sz.width(),
            (self.rect().bottom() + 1 - sz.height()) / 2)

    def _updateStyle(self):
        borderWidth = self.style().pixelMetric(QtWidgets.QStyle.PM_DefaultFrameWidth) + 1
        selectorWidth = self.selector.sizeHint().width() if self.isSelectorVisible() else 0 
        self.setStyleSheet('QLineEdit { padding-right: %ipx; }' % (selectorWidth + borderWidth))
        fm = QtGui.QFontMetrics(self.font()) # font metrics
        maxText = '9' * self._maxDigits + '. '
        self.setMinimumSize(
            fm.width(maxText) + selectorWidth + borderWidth * 2,
            max(fm.height(), self.selector.sizeHint().height() + borderWidth * 2))

    def isSelectorVisible(self): 
        return not self.selector.isHidden()
    def setSelectorVisible(self, value):
        self.selector.setVisible(value)
        self._updateStyle()
    selectorVisible = QtCore.pyqtProperty(bool, isSelectorVisible, setSelectorVisible)

    def mouseDoubleClickEvent(self, mouseEvent):
        if mouseEvent.button() == QtCore.Qt.LeftButton:
            # select all on double click, otherwise only group of digits will be selected
            self.selectAll()
            
    def keyPressEvent(self, keyEvent):
        if keyEvent.modifiers() in (QtCore.Qt.NoModifier, QtCore.Qt.KeypadModifier):
            key = keyEvent.key()
            if key == QtCore.Qt.Key_Insert:
                self.popupCalculator()
                return
            elif key in (QtCore.Qt.Key_Backspace, QtCore.Qt.Key_Delete) and not self.hasSelectedText():
                text = self.text()
                cursor_pos = self.cursorPosition()
                if key == QtCore.Qt.Key_Backspace:
                    pos_del = cursor_pos - 1 # position to check for character
                    pos_move = cursor_pos - 1 # position to move to
                else:  # key == QtCore.Qt.Key_Delete:
                    pos_del = cursor_pos
                    pos_move = cursor_pos + 1
                if 0 <= pos_del < len(text):
                    char_del = text[pos_del]
                    if (char_del == '.' and self._fractionDigits > 0) or char_del == ',':
                        # the char to be deleted is a dot or thousands separator
                        self.setCursorPosition(pos_move) # jump over the char
            elif key in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):
                self.edited.emit() # forcibly emit edited signal
                return
        super().keyPressEvent(keyEvent)

    def interactiveClear(self):
        self.clear()
        self.onTextEdited('')
    
    def clear(self):
        self.setValue(0)

    def _format(self):
        """Format the value according to the view properties (maxDigits, fractionDigits,
        thousandsSeparator)).
        Filter invalid entered symbols.
        """
        text = self.text()
        if self._fractionDigits > 0: 
            text += '.' + '0' * self._fractionDigits
        text = list(text)
        cursor_pos = self.cursorPosition()
        point_pos = -1
        i = 0
        negative = False
        while i < len(text):
            char = text[i]
            delete = False  # delete current symbol
            if char == '-': 
                negative = not negative
                delete = True
            elif i == 0 and char == '0': 
                delete = True  # leading zero
            elif char == '.':
                if point_pos == -1:
                    # we found first dot and we expect the fractional part
                    point_pos = i
                    if not self._fractionDigits:
                        # remove the rest (nothing important there) -- the dot was found, not fractional part
                        del text[i:]
                        break
                else: 
                    if self._fractionDigits == -1:
                        # second dot, length of the fractional part is not fixed
                        del text[i:] # remove the rest
                        break
                    delete = True  # found next dot
            elif not char.isdigit():
                # we checked - and ., we remove other non digits
                delete = True # non-digit
            elif point_pos == -1:
                # it's a digit, dot was not found yet
                delete = i >= self._maxDigits - max(self._fractionDigits, 0) #  отсекаем лишние цифры целой части
            else:
                # it's a digit, dot already found
                # chop redundant digits of fractional part
                delete = i - point_pos > self._fractionDigits >= 0 # or not self._fractionDigits:
            
            if delete:
                # delete current symbol
                del text[i]
                cursor_pos -= int(i < cursor_pos)
            else: 
                i += 1
            
        if self._separateThousands:
            i = point_pos if point_pos != -1 else len(text)
            while i > 3:
                i -= 3
                text.insert(i, ',')
                cursor_pos += int(i < cursor_pos)
        if not text:
            text = ['0']
            cursor_pos = 1
        if negative and not self.nonNegative:# and self.value() != Dec(0):
            text.insert(0, '-')
            cursor_pos += 1
        self.setText(''.join(text))
        self.setCursorPosition(cursor_pos)

    
    def onTextEdited(self, txt):
        """Called whenever the text is edited interactively (not programmatically like via setText()).
        Filters invalid entered symbols.
        """
        self._format()
        if self._newText is None:  # start of editing
            self._newText = self.text()

    def focusOutEvent(self, focusEvent):
        """Check for changes when leaving the widget
        """
        if focusEvent.reason() != QtCore.Qt.PopupFocusReason: # контекстное меню (или еще что) выскочило 
            if self._newText is not None: # while the widget was focused - the text was changed
                self.edited.emit()
                self._newText = None # reset the tracking
        super().focusOutEvent(focusEvent)

    def value(self): 
        """Return the decimal entered in the field.
        """
        return Decimal(self.text().replace(',', '') or 0)
    
    def setValue(self, value, emit=False):
        """Set field text for the given decimal value.

        Args:
            value (Decimal): the value to set
            emit (bool): whether to emit `edited` signal (like when the date is entered interactively)
        """
        value = Decimal(value)
        if self._fractionDigits != -1:
            value = round(value, self._fractionDigits)
        self.setText(regular_notation(value))
        self._format()
        #self.setCursorPosition(0)
        if emit:
            self.edited.emit()
    
    def popupCalculator(self):
        self.selectAll()
        PopupCalculator(self).show()
        
    def strValue(self):
        return regular_notation(self.value())
        
    def contextMenuEvent(self, qContextMenuEvent):
        self.selectAll()
        self.menu.popup(qContextMenuEvent.globalPos())


def test():
    app = QtWidgets.QApplication([])
    #m = WPopupCalculator(None, True)
    widget = DecimalEdit(None)
    widget.show()
    app.exec()


if __name__ == '__main__':
    test()
