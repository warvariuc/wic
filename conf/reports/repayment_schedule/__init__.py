from PyQt4 import QtCore, QtGui, QtWebKit

from datetime import date as Date
from dateutil.relativedelta import relativedelta as RelDelta
from decimal import Decimal as Dec
from wic.forms import WForm, setValue, getValue
from wic.widgets import w_table
from wic import w
import conf as gM



daysInYear = 365


class Form(WForm):
    
    def тест(self):
        pass

#    def on_open(self): # called by the system after it loads the Form
#        w.printMessage('Форма загружена.')
#
#        self.parentWidget().setWindowState(QtCore.Qt.WindowMaximized)
#
#        self._.dteShowSelector = self.dateEdit.selectorVisible
#        self._.dateEdit = Date.today()
#        self._.decimalEdit = '20000000.1251'
#        self.updateInfoAboutDecimalEdit()
#
#        self._.equalInstallments = True
#        self._.disbursDate = Date.today()
#        self._.firstInstallmDate = self._.disbursDate + RelDelta(months= 1)
#        self._.loanAmount = 10000
#        self._.numInstallments = 12
#        self._.flatInterest = False
#        self._.annInterestRate = 16
#        self.loanAmount.setFocus()
#
#        for i in range(4):
#            self._['weekDay' + str(i)] = True
#
#        table = w_table.WTable(self.tableView)
#        table.newColumn('НомВыпл', label= '#', defaultValue= 0, width= 30)
#        table.newColumn('ДатаВыпл', label= 'Дата', editable= True, alignment= QtCore.Qt.AlignCenter, width= 80, editedHandler= self.onTableValueEdited)
#        table.newColumn('Дней', label= 'Дней', defaultValue= 0, width= 35)
#        table.newColumn('Остаток', format= ',.2f ', defaultValue= Dec(), width= 80) # 
#        col = table.newColumn('Флаг', label= '*', defaultValue= False, editable= True, width= 25, editedHandler= self.onTableValueEdited)
#        col.headerItem.roles[QtCore.Qt.ToolTipRole] = 'Зафиксировать сумму тела займа'
#        table.newColumn('ТелоЗайма', label= 'Заём', format= ',.2f ', defaultValue= Dec(), editable= True, width= 80, editedHandler= self.onTableValueEdited)
#        table.newColumn('Проценты', format= ',.2f ', defaultValue= Dec(), width= 80)
#        table.newColumn('Всего', format= ',.2f ', defaultValue= Dec(), editable= True, width= 80, editedHandler= self.onTableValueEdited) # defaultValue = func - вычисляемое значение
#
#        boldFont = QtGui.QFont()
#        boldFont.setBold(True)
#        self.totalsTableView.insertRow(0)
#        for columnIndex in range(table.columnCount()):
#            self.totalsTableView.insertColumn(columnIndex)
#            item = QtGui.QTableWidgetItem()
#            item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
#            item.setFlags(QtCore.Qt.ItemIsEnabled)
#            item.setFont(boldFont)
#            self.totalsTableView.setItem(0, columnIndex, item)
#            self.totalsTableView.setColumnWidth(columnIndex, table.column(columnIndex).width)
#
#        self.tableView.horizontalHeader().sectionResized.connect(self.updateTotalsSectionWidth)
#        self.tableView.horizontalScrollBar().valueChanged.connect(self.totalsTableView.horizontalScrollBar().setValue)
#        
#        self.table = table
#
#    def updateTotalsSectionWidth(self, logicalIndex, oldSize, newSize):
#        self.totals.setColumnWidth(logicalIndex, newSize)
#
#    def onTableValueEdited(self, row, column, value):
#        if column.identifier == 'ТелоЗайма':
#            row.Флаг = True # сумма тела займа задана вручную
#        elif column.identifier == 'Всего':
#            row.ТелоЗайма = max(value - row.Проценты, 0) # ТелоЗайма = Всего - Проценты
#            row.Флаг = True # сумма тела займа задана вручную
#        self.РассчитатьСуммы()
#        self.ОбновитьИтоги()
#
#    def ОбновитьИтоги(self): # и ТП
#        totalDays = 0
#        totalPrincipal = Dec(0)
#        totalInterest = Dec(0)
#        totalTotal = Dec(0)
#        for row in self.table.rows():
#            row.Всего = row.ТелоЗайма + row.Проценты
#            totalPrincipal += row.ТелоЗайма
#            totalInterest += row.Проценты
#            totalTotal += row.Всего
#            totalDays += row.Дней
#    
#        self.totals.item(0, 2).setText(str(totalDays))
#        self.totals.item(0, 5).setText(format(totalPrincipal, ',f'))
#        self.totals.item(0, 6).setText(format(totalInterest, ',f'))
#        self.totals.item(0, 7).setText(format(totalTotal, ',f'))
#    
#    @QtCore.pyqtSlot()
#    def on_calculate_clicked(self):
#        if not (self._.disbursDate and self._.loanAmount and self._.numInstallments
#                and self._.annInterestRate and self._.firstInstallmDate):
#            QtGui.QMessageBox.warning(self, 'Заполните поля', 'Заполните все необходимые поля')
#        else:
#            self.РассчитатьГрафик()
#    
#    def on_loanAmount_edited(self): self.РассчитатьСуммы()
#    def on_numInstallments_edited(self): self.РассчитатьГрафик()
#    def on_annInterestRate_edited(self): self.РассчитатьСуммы()
#    def on_equalInstallments_stateChanged(self, state): self.РассчитатьСуммы()
#    def on_flatInterest_stateChanged(self, state): self.РассчитатьСуммы()
#    def on_disbursDate_edited(self): self.РассчитатьСуммы()
#    def on_firstInstallmDate_edited(self): self.РассчитатьГрафик()
#    def on_weekDay0_stateChanged(self, state): self.РассчитатьГрафик()
#    def on_weekDay1_stateChanged(self, state): self.РассчитатьГрафик()
#    def on_weekDay2_stateChanged(self, state): self.РассчитатьГрафик()
#    def on_weekDay3_stateChanged(self, state): self.РассчитатьГрафик()
#    def on_weekDay4_stateChanged(self, state): self.РассчитатьГрафик()
#    def on_weekDay5_stateChanged(self, state): self.РассчитатьГрафик()
#    def on_weekDay6_stateChanged(self, state): self.РассчитатьГрафик()
#    
#    @QtCore.pyqtSlot()
#    def on_printButton_clicked(self):
#        webView = QtWebKit.QWebView()
#        html = '<html><head></head><body>'
#        html += '<h3>График платежей по займу</h3>'
#        html += '<table border cellpadding="3" cellspacing="0">'
#        html += '\n<tr><td align="right"><b>#</b><td align="center"><b>Дата</b><td align="right"><b>Дней</b><td align="right"><b>Остаток</b><td align="right"><b>Заём</b><td align="right"><b>Проценты</b><td align="right"><b>Всего</b>'
#        for row in self.table.rows():
#            html += '\n\t<tr>\n\t\t'
#            html += '<td align="right">{НомВыпл}<td align="center">{ДатаВыпл:%m.%d.%Y}<td align="right">{Дней}'\
#                    '<td align="right">{Остаток:,.2f}<td align="right">{ТелоЗайма:,.2f}'\
#                    '<td align="right">{Проценты:,.2f}<td align="right">{Всего:,.2f}'.format(
#                    НомВыпл= row.НомВыпл, ДатаВыпл= row.ДатаВыпл, Дней= row.Дней, Остаток= row.Остаток,
#                    ТелоЗайма= row.ТелоЗайма, Проценты= row.Проценты, Всего= row.Всего)
#        html += '\n</table></body></html>'
#        webView.setHtml(html)
#    
#        window = w.mainWindow.mdiArea.addSubWindow(webView)
#        window.setWindowTitle('Печать графика')
#        window.show()
#    
#        printer = QtGui.QPrinter()
#        printDialog = QtGui.QPrintPreviewDialog(printer)
#        #printDialog.printer()->setPaperSize(QPrinter::A4);
#        #printDialog.printer()->setOrientation(QPrinter::Portrait);
#        #printDialog.printer()->setPageMargins(10.0,10.0,10.0,10.0,QPrinter::Millimeter);
#        #printDialog.printer()->setFullPage(true);
#        printDialog.paintRequested.connect(webView.print)
#        #connect(&printDialog, SIGNAL(paintRequested(QPrinter *)), m_ui->webView, SLOT(print(QPrinter *)));
#        printDialog.exec()
#
#    def РассчитатьСуммы(self):
#        if not (self._.disbursDate and self._.loanAmount and self._.numInstallments
#                and self._.annInterestRate and self.table.rowCount()):
#            return
#        if not self._.firstInstallmDate:
#            self._.firstInstallmDate = self._.disbursDate + RelDelta(months= 1)
#    #    Состояние ( "Идет расчет..." );
#        СутПроцСтавка = self._.annInterestRate / 100 / daysInYear
#        tbl = self.table.copy() # предполагается, что даты уже рассчитаны
#        КолвоАвто = self.table.rowCount()
#        СуммаАвто = self._.loanAmount
#        ПредДата = self._.disbursDate
#    
#        for row in tbl.rows():
#            row.Дней = (row.ДатаВыпл - ПредДата).days # количество дней между выплатами
#            ПредДата = row.ДатаВыпл
#            if row.Флаг:
#                КолвоАвто -= 1 # количество и...
#                СуммаАвто -= row.ТелоЗайма #...сумма отведенная на автоматически рассчитываемые выплаты
#    
#        if not КолвоАвто: return
#    
#        if self._.equalInstallments:
#            МинРавн = Dec(0)
#            МаксРавн = self._.loanAmount * 2
#            Порог = self._.numInstallments / 200
#            while True:
#                ОстатокЗайма = self._.loanAmount
#                Равн = round((МинРавн + МаксРавн) / 2, 2) # метод деления пополам
#                for row in tbl.rows():
#                    row.Проценты = round((self._.loanAmount if self._.flatInterest else ОстатокЗайма) * СутПроцСтавка * row.Дней, 2)
#                    if not row.Флаг:
#                        row.ТелоЗайма = Равн - row.Проценты
#    #                           //Если Табл.ТелоЗайма<0 Тогда
#    #                            //    Предупреждение("При заданных параметрах не удается рассчитать равные выплаты. 
#    #                           //        |Попытайтесь уменьшить количество выплат или другие параметры.");
#    #                   //    Возврат;
#                    ОстатокЗайма -= row.ТелоЗайма
#                    row.Остаток = ОстатокЗайма
#    #                    Сообщить("МинРавн = " + МинРавн + "; МаксРавн = " + МаксРавн + "; Равн = " + Равн + "; Остаток = " + ОстатокЗайма);
#                if ОстатокЗайма < 0:
#                    МаксРавн = Равн
#                else:
#                    МинРавн = Равн
#                if abs(ОстатокЗайма) <= Порог or МаксРавн - МинРавн <= Dec('0.01'): break
#        else:
#            Равн = round(СуммаАвто / КолвоАвто, 2)
#    
#        ОстатокЗайма = self._.loanAmount
#        for rowIndex in range(self.table.rowCount()):
#            row = self.table.row(rowIndex)
#            row1 = tbl.row(rowIndex)
#            row.Дней = row1.Дней
#            row.Остаток = ОстатокЗайма
#    #        Если Вручную = 0 Тогда 
#            row.Проценты = round(СутПроцСтавка * row.Дней * (self._.loanAmount if self._.flatInterest else row.Остаток), 2)
#            if not row.Флаг:
#                row.ТелоЗайма = СуммаАвто if КолвоАвто == 1 else (Равн - row1.Проценты if self._.equalInstallments else Равн)
#                СуммаАвто -= row.ТелоЗайма
#                КолвоАвто -= 1
#    #        КонецЕсли;
#            ОстатокЗайма -= row.ТелоЗайма
#        self.ОбновитьИтоги()
#    
#    def РассчитатьГрафик(self):
#        self.РассчитатьДаты()
#        self.РассчитатьСуммы()
#        
#    def РассчитатьДаты(self):
#        if not (self._.disbursDate and self._.numInstallments
#            and self._.firstInstallmDate): return
#        self.table.delRows()
#        for НомВыпл in range(int(self._.numInstallments)):
#            row = self.table.newRow()
#            row.НомВыпл = НомВыпл + 1
#            row.ДатаВыпл = self._.firstInstallmDate + RelDelta(months= НомВыпл)
#    
#            for i in range(6):
#                if self._['weekDay' + str(row.ДатаВыпл.dayOfWeek())]:
#                    break
#                row.ДатаВыпл += RelDelta(days= 1)
        