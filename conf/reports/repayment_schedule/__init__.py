from PyQt4 import QtCore, QtGui, QtWebKit

from wic.datetime import Date, RelDelta
from decimal import Decimal as Dec
from wic.forms import WForm
from wic import w_table
from wic import w



daysInYear = 365


class Form(WForm):
    
    def onOpen(self): # called by the system after it loads the Form

        self._.equalInstallments = True
        self._.disbursDate = Date.today()
        self._.firstInstallmDate = self._.disbursDate + RelDelta(months= 1)
        self._.loanAmount = 10000
        self._.numInstallments = 12
        self._.annInterestRate = 16
        self._.flatInterest = False
        self.loanAmount.setFocus()

        for i in range(4):
            self._['weekDay%d' % i] = True

        table = w_table.WTable(self.tableView)
        table.newColumn('RepaymentNo', label= '#', defaultValue= 0, width= 30)
        table.newColumn('RepaymentDate', label= 'Date', editable= True, alignment= QtCore.Qt.AlignCenter, width= 80, onEdited= self.onTableValueEdited)
        table.newColumn('DaysCount', label= 'Days', defaultValue= 0, width= 35)
        table.newColumn('Balance', format= ',.2f ', defaultValue= Dec(), width= 80) # 
        col = table.newColumn('Flag', label= '*', defaultValue= False, editable= True, width= 25, onEdited= self.onTableValueEdited)
        col.headerItem.roles[QtCore.Qt.ToolTipRole] = 'Fixed principal'
        table.newColumn('Principal', format= ',.2f ', defaultValue= Dec(), editable= True, width= 80, onEdited= self.onTableValueEdited)
        table.newColumn('Interest', format= ',.2f ', defaultValue= Dec(), width= 80)
        table.newColumn('Total', format= ',.2f ', defaultValue= Dec(), editable= True, width= 80, onEdited= self.onTableValueEdited) # defaultValue = func - вычисляемое значение

        boldFont = QtGui.QFont()
        boldFont.setBold(True)
        self.totalsTableView.insertRow(0)
        for columnIndex in range(table.columnCount()):
            self.totalsTableView.insertColumn(columnIndex)
            item = QtGui.QTableWidgetItem()
            item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            item.setFont(boldFont)
            self.totalsTableView.setItem(0, columnIndex, item)
            self.totalsTableView.setColumnWidth(columnIndex, table.column(columnIndex).width)

        self.tableView.horizontalHeader().sectionResized.connect(self.updateTotalsSectionWidth)
        self.tableView.horizontalScrollBar().valueChanged.connect(self.totalsTableView.horizontalScrollBar().setValue)
        
        self.table = table

        self.loanAmount.edited.connect(self.CalculateAmounts)
        self.numInstallments.edited.connect(self.CalculateSchedule)
        self.annInterestRate.edited.connect(self.CalculateAmounts)
        self.equalInstallments.stateChanged.connect(self.CalculateAmounts)
        self.flatInterest.stateChanged.connect(self.CalculateAmounts)
        self.disbursDate.edited.connect(self.CalculateAmounts)
        self.firstInstallmDate.edited.connect(self.CalculateSchedule)
        self.weekDay0.stateChanged.connect(self.CalculateSchedule)
        self.weekDay1.stateChanged.connect(self.CalculateSchedule)
        self.weekDay2.stateChanged.connect(self.CalculateSchedule)
        self.weekDay3.stateChanged.connect(self.CalculateSchedule)
        self.weekDay4.stateChanged.connect(self.CalculateSchedule)
        self.weekDay5.stateChanged.connect(self.CalculateSchedule)
        self.weekDay6.stateChanged.connect(self.CalculateSchedule)


    def updateTotalsSectionWidth(self, logicalIndex, oldSize, newSize):
        self.totalsTableView.setColumnWidth(logicalIndex, newSize)

    def onTableValueEdited(self, row, column, value):
        if column.identifier == 'Principal':
            row.Flag = True # сумма тела займа задана вручную
        elif column.identifier == 'Total':
            row.Principal = max(value - row.Interest, 0) # Principal = Total - Interest
            row.Flag = True # сумма тела займа задана вручную
        self.CalculateAmounts()
        self.RefreshTotals()

    def RefreshTotals(self):
        totalDays = 0
        totalPrincipal = Dec(0)
        totalInterest = Dec(0)
        totalTotal = Dec(0)
        for row in self.table.rows():
            row.Total = row.Principal + row.Interest
            totalPrincipal += row.Principal
            totalInterest += row.Interest
            totalTotal += row.Total
            totalDays += row.DaysCount
    
        self.totalsTableView.item(0, 2).setText(str(totalDays))
        self.totalsTableView.item(0, 5).setText(format(totalPrincipal, ',f'))
        self.totalsTableView.item(0, 6).setText(format(totalInterest, ',f'))
        self.totalsTableView.item(0, 7).setText(format(totalTotal, ',f'))
    
    @QtCore.pyqtSlot()
    def on_calculate_clicked(self):
        if not (self._.disbursDate and self._.loanAmount and self._.numInstallments
                and self._.annInterestRate and self._.firstInstallmDate):
            QtGui.QMessageBox.warning(self, 'Заполните поля', 'Заполните все необходимые поля')
        else:
            self.CalculateSchedule()
    
    def CalculateSchedule(self):
        self.CalculateDates()
        self.CalculateAmounts()
        
    def CalculateDates(self):
        if self._.disbursDate and self._.numInstallments and self._.firstInstallmDate: 
            self.table.delRows()
            for RepaymentNo in range(int(self._.numInstallments)):
                row = self.table.newRow()
                row.RepaymentNo = RepaymentNo + 1
                row.RepaymentDate = self._.firstInstallmDate + RelDelta(months= RepaymentNo)
        
                for i in range(6):
                    if self._['weekDay%d' % row.RepaymentDate.weekday()]:
                        break
                    row.RepaymentDate += RelDelta(days= 1)
                
    def CalculateAmounts(self):
        if self._.disbursDate and self._.loanAmount and self._.numInstallments \
                and self._.annInterestRate and self.table.rowCount():
            if not self._.firstInstallmDate:
                self._.firstInstallmDate = self._.disbursDate + RelDelta(months= 1)
        #    Состояние ( "Идет расчет..." );
            dailyInterestRate = self._.annInterestRate / 100 / daysInYear
            tbl = self.table.copy() # предполагается, что даты уже рассчитаны
            countAuto = self.table.rowCount()
            amountAuto = self._.loanAmount
            prevDate = self._.disbursDate
        
            for row in tbl.rows():
                row.DaysCount = (row.RepaymentDate - prevDate).days # количество дней между выплатами
                prevDate = row.RepaymentDate
                if row.Flag:
                    countAuto -= 1 # количество и...
                    amountAuto -= row.Principal #...сумма отведенная на автоматически рассчитываемые выплаты
        
            if countAuto:
                if self._.equalInstallments:
                    minEqual = Dec(0)
                    maxEqual = self._.loanAmount * 2
                    threshold = self._.numInstallments / 200
                    while True:
                        PrincipalBalance = self._.loanAmount
                        equal = round((minEqual + maxEqual) / 2, 2) # метод деления пополам
                        for row in tbl.rows():
                            row.Interest = round((self._.loanAmount if self._.flatInterest else PrincipalBalance) * dailyInterestRate * row.DaysCount, 2)
                            if not row.Flag:
                                row.Principal = equal - row.Interest
            #                           //Если Табл.Principal<0 Тогда
            #                            //    Предупреждение("При заданных параметрах не удается рассчитать равные выплаты. 
            #                           //        |Попытайтесь уменьшить количество выплат или другие параметры.");
            #                   //    Возврат;
                            PrincipalBalance -= row.Principal
                            row.Balance = PrincipalBalance
            #                    Сообщить("minEqual = " + minEqual + "; maxEqual = " + maxEqual + "; equal = " + equal + "; Balance = " + PrincipalBalance);
                        if PrincipalBalance < 0:
                            maxEqual = equal
                        else:
                            minEqual = equal
                        if abs(PrincipalBalance) <= threshold or maxEqual - minEqual <= Dec('0.01'): break
                else:
                    equal = round(amountAuto / countAuto, 2)
            
                PrincipalBalance = self._.loanAmount
                for rowIndex in range(self.table.rowCount()):
                    row = self.table.row(rowIndex)
                    row1 = tbl.row(rowIndex)
                    row.DaysCount = row1.DaysCount
                    row.Balance = PrincipalBalance
            #        Если Вручную = 0 Тогда 
                    row.Interest = round(dailyInterestRate * row.DaysCount * (self._.loanAmount if self._.flatInterest else row.Balance), 2)
                    if not row.Flag:
                        row.Principal = amountAuto if countAuto == 1 else (equal - row1.Interest if self._.equalInstallments else equal)
                        amountAuto -= row.Principal
                        countAuto -= 1
            #        КонецЕсли;
                    PrincipalBalance -= row.Principal
                self.RefreshTotals()

    @QtCore.pyqtSlot()
    def on_printButton_clicked(self):
        webView = QtWebKit.QWebView()
        html = '<html><head></head><body>'
        html += '<h3>Loan repayment schedule</h3>'
        html += '<table border cellpadding="3" cellspacing="0">'
        html += '\n<tr><td align="right"><b>#</b><td align="center"><b>Date</b><td align="right"><b>Days</b><td align="right"><b>Balance</b><td align="right"><b>Principal</b><td align="right"><b>Interest</b><td align="right"><b>Total</b>'
        for row in self.table.rows():
            html += '\n\t<tr>\n\t\t'
            html += '<td align="right">{RepaymentNo}<td align="center">{RepaymentDate:%m.%d.%Y}<td align="right">{DaysCount}'\
                    '<td align="right">{Balance:,.2f}<td align="right">{Principal:,.2f}'\
                    '<td align="right">{Interest:,.2f}<td align="right">{Total:,.2f}'.format(
                    RepaymentNo= row.RepaymentNo, RepaymentDate= row.RepaymentDate, DaysCount= row.DaysCount, Balance= row.Balance,
                    Principal= row.Principal, Interest= row.Interest, Total= row.Total)
        html += '\n</table></body></html>'
        webView.setHtml(html)
    
        window = w.mainWindow.mdiArea.addSubWindow(webView)
        window.setWindowTitle('Print schedule')
        window.show()
    
        printer = QtGui.QPrinter()
        printDialog = QtGui.QPrintPreviewDialog(printer)
        #printDialog.printer()->setPaperSize(QPrinter::A4);
        #printDialog.printer()->setOrientation(QPrinter::Portrait);
        #printDialog.printer()->setPageMargins(10.0,10.0,10.0,10.0,QPrinter::Millimeter);
        #printDialog.printer()->setFullPage(true);
        printDialog.paintRequested.connect(webView.print)
        printDialog.exec()
