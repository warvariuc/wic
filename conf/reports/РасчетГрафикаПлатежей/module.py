from PyQt4 import QtCore, QtGui, QtWebKit
from w_date import Date
from decimal import Decimal as Dec
import w_table
import w, gM

table = None


def РассчитатьДаты():
    if not (widgets.disbursDate and widgets.numInstallments
        and widgets.firstInstallmDate): return
    table.delRows()
    for НомВыпл in range(int(widgets.numInstallments)):
        row = table.newRow()
        row.НомВыпл = НомВыпл + 1
        row.ДатаВыпл = widgets.firstInstallmDate.addMonths(НомВыпл)

        for i in range(6):
            if widgets['weekDay' + str(row.ДатаВыпл.dayOfWeek())]:
                break
            row.ДатаВыпл += 1


daysInYear = 365

def РассчитатьСуммы():
    if not (widgets.disbursDate and widgets.loanAmount and widgets.numInstallments
            and widgets.annInterestRate and table.rowCount()):
        return
    if not widgets.firstInstallmDate: 
        widgets.firstInstallmDate = widgets.disbursDate.addMonths(1)
#	Состояние ( "Идет расчет..." );
    СутПроцСтавка = widgets.annInterestRate / 100 / daysInYear
    tbl = table.copy() # предполагается, что даты уже рассчитаны
    КолвоАвто = table.rowCount()
    СуммаАвто = widgets.loanAmount
    ПредДата = widgets.disbursDate

    for row in tbl.rows():
        row.Дней =row.ДатаВыпл - ПредДата # количество дней между выплатами
        ПредДата = row.ДатаВыпл
        if row.Флаг:
            КолвоАвто -= 1 # количество и...
            СуммаАвто -= row.ТелоЗайма #...сумма отведенная на автоматически рассчитываемые выплаты

    if not КолвоАвто: return
    
    if widgets.equalInstallments:
        МинРавн = Dec(0)
        МаксРавн = widgets.loanAmount * 2
        Порог = widgets.numInstallments / 200
        while True:
            ОстатокЗайма = widgets.loanAmount
            Равн = round((МинРавн + МаксРавн) / 2, 2) # метод деления пополам
            for row in tbl.rows():
                row.Проценты = round((widgets.loanAmount if widgets.flatInterest else ОстатокЗайма) * СутПроцСтавка * row.Дней, 2)
                if not row.Флаг:
                    row.ТелоЗайма = Равн - row.Проценты
#       					//Если Табл.ТелоЗайма<0 Тогда
#			        		//	Предупреждение("При заданных параметрах не удается рассчитать равные выплаты. 
#					       //		|Попытайтесь уменьшить количество выплат или другие параметры.");
#                   //	Возврат;
                ОстатокЗайма -= row.ТелоЗайма
                row.Остаток = ОстатокЗайма
#			        Сообщить("МинРавн = " + МинРавн + "; МаксРавн = " + МаксРавн + "; Равн = " + Равн + "; Остаток = " + ОстатокЗайма);
            if ОстатокЗайма < 0:
                МаксРавн = Равн
            else:
                МинРавн = Равн
            if abs(ОстатокЗайма) <= Порог or МаксРавн - МинРавн <= Dec('0.01'): break
    else:
        Равн = round(СуммаАвто / КолвоАвто, 2)

    ОстатокЗайма = widgets.loanAmount
    for rowIndex in range(table.rowCount()):
        row = table.row(rowIndex)
        row1 = tbl.row(rowIndex)
        row.Дней = row1.Дней
        row.Остаток = ОстатокЗайма
#		Если Вручную = 0 Тогда 
        row.Проценты = round(СутПроцСтавка * row.Дней * (widgets.loanAmount if widgets.flatInterest else row.Остаток), 2)
        if not row.Флаг:
            row.ТелоЗайма = СуммаАвто if КолвоАвто == 1 else (Равн - row1.Проценты if widgets.equalInstallments else Равн)
            СуммаАвто -= row.ТелоЗайма
            КолвоАвто -= 1
#		КонецЕсли;
        ОстатокЗайма -= row.ТелоЗайма
    ОбновитьИтоги()

def РассчитатьГрафик():
    РассчитатьДаты()
    РассчитатьСуммы()


def ОбновитьИтоги(): # и ТП
    totalDays = 0
    totalPrincipal = Dec(0)
    totalInterest = Dec(0)
    totalTotal = Dec(0)
    for row in table.rows():
        row.Всего = row.ТелоЗайма + row.Проценты
        totalPrincipal += row.ТелоЗайма
        totalInterest += row.Проценты
        totalTotal += row.Всего
        totalDays += row.Дней
    
    form.totals.item(0, 2).setText(str(totalDays))
    form.totals.item(0, 5).setText(format(totalPrincipal, ',f'))
    form.totals.item(0, 6).setText(format(totalInterest, ',f'))
    form.totals.item(0, 7).setText(format(totalTotal, ',f'))


def calculate_clicked(checked=False):
    if not (widgets.disbursDate and widgets.loanAmount and widgets.numInstallments
            and widgets.annInterestRate and widgets.firstInstallmDate):
        QtGui.QMessageBox.warning(form, 'Заполните поля', 'Заполните все необходимые поля')
        return
    РассчитатьГрафик()

def loanAmount_edited(): РассчитатьСуммы()
def numInstallments_edited(): РассчитатьГрафик()
def annInterestRate_edited(): РассчитатьСуммы()
def equalInstallments_stateChanged(state): РассчитатьСуммы()
def flatInterest_stateChanged(state): РассчитатьСуммы()
def disbursDate_edited(): РассчитатьСуммы()
def firstInstallmDate_edited(): РассчитатьГрафик()
def weekDay0_stateChanged(state): РассчитатьГрафик()
def weekDay1_stateChanged(state): РассчитатьГрафик()
def weekDay2_stateChanged(state): РассчитатьГрафик()
def weekDay3_stateChanged(state): РассчитатьГрафик()
def weekDay4_stateChanged(state): РассчитатьГрафик()
def weekDay5_stateChanged(state): РассчитатьГрафик()
def weekDay6_stateChanged(state): РассчитатьГрафик()

def printButton_clicked(checked=False):
    webView = QtWebKit.QWebView()
    html = '<html><head></head><body>'
    html += '<h3>График платежей по займу</h3>'
    html += '<table border cellpadding="3" cellspacing="0">'
    html += '\n<tr><td align="right"><b>#</b><td align="center"><b>Дата</b><td align="right"><b>Дней</b><td align="right"><b>Остаток</b><td align="right"><b>Заём</b><td align="right"><b>Проценты</b><td align="right"><b>Всего</b>'
    for row in table.rows():
        html += '\n\t<tr>\n\t\t'
        html += '<td align="right">{НомВыпл}<td align="center">{ДатаВыпл:%m.%d.%Y}<td align="right">{Дней}'\
                '<td align="right">{Остаток:,.2f}<td align="right">{ТелоЗайма:,.2f}'\
                '<td align="right">{Проценты:,.2f}<td align="right">{Всего:,.2f}'.format(
                НомВыпл=row.НомВыпл, ДатаВыпл=row.ДатаВыпл, Дней=row.Дней, Остаток=row.Остаток, 
                ТелоЗайма=row.ТелоЗайма, Проценты=row.Проценты, Всего=row.Всего)
    html += '\n</table></body></html>'
    webView.setHtml(html)

    window = w.mainWindow.mdiArea.addSubWindow(webView)
    window.setWindowTitle('Печать графика')
    window.show()

    printer = QtGui.QPrinter()
    printDialog = QtGui.QPrintPreviewDialog(printer)
    #printDialog.printer()->setPaperSize(QPrinter::A4);
    #printDialog.printer()->setOrientation(QPrinter::Portrait);
    #printDialog.printer()->setPageMargins(10.0,10.0,10.0,10.0,QPrinter::Millimeter);
    #printDialog.printer()->setFullPage(true);
    printDialog.paintRequested.connect(webView.print)
    #connect(&printDialog, SIGNAL(paintRequested(QPrinter *)), m_ui->webView, SLOT(print(QPrinter *)));
    printDialog.exec()


def handleTableValueEdited(row, column, value):
    if column.identifier == 'ТелоЗайма':
        row.Флаг = True # сумма тела займа задана вручную
    elif column.identifier == 'Всего':
        row.ТелоЗайма = max(value - row.Проценты, 0) # ТелоЗайма = Всего - Проценты
        row.Флаг = True # сумма тела займа задана вручную
    РассчитатьСуммы()
    ОбновитьИтоги()


def module_loaded(): # event called by m_py after it loads module
    return True # аналог СтатусВозврата (1) в 1С

def form_loaded(): # event called by after the form has been loaded

    form.parentWidget().setWindowState(QtCore.Qt.WindowMaximized)
    
    widgets.equalInstallments = True
    widgets.disbursDate = Date.today()
    widgets.firstInstallmDate = widgets.disbursDate.addMonths(1)
    widgets.loanAmount = 10000
    widgets.numInstallments = 12
    widgets.flatInterest = False
    widgets.annInterestRate = 16
    form.loanAmount.setFocus()

    for i in range(4): widgets['weekDay' + str(i)] = True
    
    global table
    table = w_table.WTable(form.table)
    table.newColumn('НомВыпл', label='#',defaultValue=0, width=30)
    table.newColumn('ДатаВыпл', label='Дата', editable=True, alignment=QtCore.Qt.AlignCenter, width=80, editedHandler=handleTableValueEdited)
    table.newColumn('Дней', label='Дней', defaultValue=0, width=35)
    table.newColumn('Остаток', format=',.2f ', defaultValue=Dec(), width=80) # 
    col = table.newColumn('Флаг', label='*', defaultValue=False, editable=True, width=25, editedHandler=handleTableValueEdited)
    col.headerItem.roles[QtCore.Qt.ToolTipRole] = 'Зафиксировать сумму тела займа'
    table.newColumn('ТелоЗайма', label='Заём', format=',.2f ', defaultValue=Dec(), editable=True, width=80, editedHandler=handleTableValueEdited)
    table.newColumn('Проценты', format=',.2f ', defaultValue=Dec(), width=80)
    table.newColumn('Всего', format=',.2f ', defaultValue=Dec(), editable=True, width=80, editedHandler=handleTableValueEdited) # defaultValue = func - вычисляемое значение
    
    boldFont = QtGui.QFont()
    boldFont.setBold(True)
    form.totals.insertRow(0)
    for columnIndex in range(table.columnCount()):
        form.totals.insertColumn(columnIndex)
        item = QtGui.QTableWidgetItem()
        item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        item.setFlags(QtCore.Qt.ItemIsEnabled)
        item.setFont(boldFont)
        form.totals.setItem(0, columnIndex, item)
        form.totals.setColumnWidth(columnIndex, table.column(columnIndex).width)
        
    form.table.horizontalHeader().sectionResized.connect(updateTotalsSectionWidth)
    form.table.horizontalScrollBar().valueChanged.connect(form.totals.horizontalScrollBar().setValue)
    
def updateTotalsSectionWidth(logicalIndex, oldSize, newSize):
    form.totals.setColumnWidth(logicalIndex, newSize)

def form_aboutToClose() : # form is asked to close
    pass
