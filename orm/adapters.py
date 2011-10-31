'''Author: Victor Varvariuc <victor.varvariuc@gmail.com'''

'''This module contains database adapters, which incapsulate all operations specific to a certain database.
All other ORM modules should be database agnostic.'''

import os, sys, base64, locale
import time
from collections import OrderedDict

import orm
from sre_parse import isname


drivers = []

try:
    from sqlite3 import dbapi2 as sqlite3
    drivers.append('SQLite3')
except ImportError:
    orm.logger.debug('no sqlite3.dbapi2 driver')



class Adapter():
    '''Generic DB adapter.'''
    def __init__(self, uri= '', connect= True, autocommit= True):
        '''URI is already without protocol.'''
        print('Creating adapter: %s' % uri)
        self._timings = []
        if connect:
            self.connection = self.connect()
            self.cursor = self.connection.cursor()
        else:
            self.connection = None
            self.cursor = None
        self.autocommit = autocommit
    
    def connect(self):
        '''Connect to the DB and return the connection'''
        return None # DB connection

    def commit(self):
        return self.connection.commit()

    def _autocommit(self):
        '''Commit if autocommit is set.'''
        if self.autocommit:
            self.commit()

    def rollback(self):
        return self.connection.rollback()

    def close(self):
        return self.connection.close()

    def logExecute(self, *a, **b):
        lastQuery = a[0]
        t0 = time.time()
        try:
            result = self.cursor.execute(*a, **b)
        except:
            print(lastQuery)
            raise
        self._timings.append((lastQuery, time.time() - t0))
        return result
    
    def getLastQuery(self):
        return self._timings[-1]

    def execute(self, *args, **kwargs):
        return self.logExecute(*args, **kwargs)

    def AND(self, left, right):
        '''Render the AND clause.'''
        return '(%s AND %s)' % (self.render(left), self.render(right, left))

    def OR(self, left, right):
        '''Render the OR clause.'''
        return '(%s OR %s)' % (self.render(left), self.render(right, left))
    
    def EQ(self, left, right):
        if right is None:
            return '(%s IS NULL)' % self.render(left)
        return '(%s = %s)' % (self.render(left), self.render(right, left))

    def NE(self, left, right):
        if right is None:
            return '(%s IS NOT NULL)' % self.render(left)
        return '(%s <> %s)' % (self.render(left), self.render(right, left))

    def GT(self, left, right):
        return '(%s > %s)' % (self.render(left), self.render(right, left))

    def GE(self, left, right):
        return '(%s >= %s)' % (self.render(left), self.render(right, left))

    def LT(self, left, right):
        return '(%s < %s)' % (self.render(left), self.render(right, left))

    def LE(self, left, right):
        return '(%s <= %s)' % (self.render(left), self.render(right, left))

    def ADD(self, left, right):
        return '(%s + %s)' % (self.render(left), self.render(right, left))
    
    def IN(self, first, second):
        if isinstance(second, str):
            return '(%s IN (%s))' % (self.render(first), second[:-1])
        items = ', '.join(self.render(item, first) for item in second)
        return '(%s IN (%s))' % (self.render(first), items)

    def COUNT(self, expression):
        expression = '*' if orm.isModel(expression) else self.render(expression)
        distinct = getattr(expression, 'distinct', False)
        if distinct:
            return 'COUNT(DISTINCT %s)' % expression
        else:
            return 'COUNT(%s)' % expression

    def MAX(self, expression):
        return 'MAX(%s)' % self.render(expression)
    
    def MIN(self, expression):
        return 'MIN(%s)' % self.render(expression)
    
    def render(self, value, castField= None):
        '''Render of a value in a format suitable for operations with this DB field'''
        if isinstance(value, orm.fields.Expression): # it's an expression
            return value._render(self) # render sub-expression
        else: # it's a value for a DB column
            if value is not None and castField is not None:
                assert isinstance(castField, orm.fields.Expression), 'Cast field must be an Expression.'
                if isinstance(castField, orm.fields.Field): # Field - subclass of Expression
                    pass #
                else: # is the Expression itself
                    castField = castField.type # expression right operand type
                value = castField._cast(value)
                try:
                    return self._render(value, castField.column)
                except:
                    print('Check %r._cast().' % castField)
                    raise
            return self._render(value, None)
        
    def _render(self, value, column):
        if value is None:
            return self.NULL()
        if isinstance(column, Column):
            renderFunc = getattr(self, 'render' + column.type.capitalize(), None)
            if hasattr(renderFunc, '__call__'): 
                return renderFunc(value)
        return "'%s'" % value  

    def IntegrityError(self): 
        return self.driver.IntegrityError
    
    def OperationalError(self): 
        return self.driver.OperationalError

    def _getCreateTableColumns(self, table):
        columns = []
        for field in table:
            column = field.column
            if column is not None:
                colFunc = getattr(self, 'type' + column.type.capitalize())
                columnType = colFunc(**column.props)
                columns.append('%s %s' % (column.name, columnType))
        return columns
    
    def _getCreateTableIndexes(self, table):
        indexes = []
        for index in table._indexes:
            if index.type == 'primary':
                indexType = 'PRIMARY KEY'
            elif index.type == 'unique':
                indexType = 'UNIQUE KEY'
            else:
                indexType = 'KEY'
            columns = []
            for i, field in enumerate(index.fields):
                column = field.column.name
                prefixLength = index.prefixLengths[i] 
                if prefixLength:
                    column += '(%i)' % prefixLength
                sortOrder = index.sortOrders[i]
                column += ' %s' % sortOrder.upper()
                columns.append(column)
                
            indexes.append('%s %s (%s)' % (indexType, index.name, ', '.join(columns)))
            
        return indexes

    def _getCreateTableOther(self, table):
        return ''

    def getCreateTableQuery(self, table):
        '''Get CREATE TABLE statement for this database'''
        assert orm.isModel(table), 'Provide a Table subclass.'
        
        columns = self._getCreateTableColumns(table)
        indexes = self._getCreateTableIndexes(table)
        other = self._getCreateTableOther(table)
        query = 'CREATE TABLE %s (' % str(table)
        query += '\n  ' + ',\n  '.join(columns)
        query += ',\n  ' + ',\n  '.join(indexes)
        query += '\n) ' + other + ';'
        return query

    def NULL(self):   
        return 'NULL'
        
    def RANDOM(self):
        return 'RANDOM()'

    def typeInt(self, bytesCount= 4, intMap= [(1, 'TINYINT'), (2, 'SMALLINT'), 
                    (3, 'MEDIUMINT'), (4, 'INT'), (8, 'BIGINT')], autoincrement= False, **kwargs):
        '''INT column type.'''
        for _bytesCount, _columnType in intMap:
            if bytesCount <= _bytesCount:
                break
        else:
            raise Exception('Too many bytes specified.')
        if autoincrement:
            _columnType += ' AUTO_INCREMENT'
        return _columnType
    
    def renderInt(self, value):
        return str(int(value))

    def renderStr(self, value):
        return "'%s'" % value

    def renderBlob(self, value):
        return base64.b64encode(str(value))
    
    def typeDecimal(self, maxDigits, decimalPlaces= 0, **kwargs):
        '''The declaration syntax for a DECIMAL column is DECIMAL(M,D). The ranges of values for the arguments in MySQL 5.1 are as follows:
        M is the maximum number of digits (the precision). It has a range of 1 to 65. (Older versions of MySQL permitted a range of 1 to 254.)
        D is the number of digits to the right of the decimal point (the scale). It has a range of 0 to 30 and must be no larger than M.'''
        return 'DECIMAL (%s, %s)' % (maxDigits, decimalPlaces)
    
    def typeChar(self, maxLength, lengthFixed= False, **kwargs):
        '''CHAR, VARCHAR'''
        if lengthFixed:
            return 'CHAR(%i)' % maxLength
        else:
            return 'VARCHAR(%i)' % maxLength
            
    def getExpressionTables(self, expression):
        '''Get tables involved in WHERE expression.'''
        tables = set()
        if orm.isModel(expression):
            tables.add(expression)
        elif isinstance(expression, orm.Field):
            tables.add(expression.table)
        elif isinstance(expression, orm.Expression):
            tables |= self.getExpressionTables(expression.left)
            tables |= self.getExpressionTables(expression.right)
        return tables

    def lastInsertId(self):
        return None
    
    def _insert(self, *fields):
        '''Create and return INSERT query.'''
        table = None
        for item in fields:
            assert isinstance(item, (list, tuple)) and len(item) == 2, 'Pass tuples with 2 items: (field, value).'
            field, value = item
            assert isinstance(field, orm.Field), 'First item must be a Field.'
            _table = field.table
            table = table or _table
            assert table is _table, 'Pass fields from the same table'
        keys = ', '.join(field.name for field, value in fields)
        values = ', '.join(self.render(value, field) for field, value in fields)
        return 'INSERT INTO %s (%s) VALUES (%s);' % (table, keys, values)

    def insert(self, *fields):
        query = self._insert(*fields)
        result = self.execute(query)
        self._autocommit()
        return result
    
    def _update(self, *fields, where= None):
        table = None
        for item in fields:
            assert isinstance(item, (list, tuple)) and len(item) == 2, 'Pass tuples with 2 items: (field, value).'
            field, value = item
            assert isinstance(field, orm.Field), 'First item in the tuple must be a Field.'
            _table = field.table
            table = table or _table
            assert table is _table, 'Pass fields from the same table'
        sql_w = ' WHERE ' + self.render(where) if where else ''
        sql_v = ', '.join(['%s= %s' % (field.name, self.render(value, field)) for (field, value) in fields])
        return 'UPDATE %s SET %s%s;' % (table, sql_v, sql_w)

    def update(self, *fields, where= None):
        sql = self._update(*fields, where= where)
        self.execute(sql)
        try:
            return self.cursor.rowcount
        except:
            return None

    def _delete(self, table, where):
        assert orm.isModel(table)
        sql_w = ' WHERE ' + self.render(where) if where else ''
        return 'DELETE FROM %s%s;' % (table, sql_w)

    def delete(self, table, where):
        sql = self._delete(table, where)
        self.execute(sql)
        try:
            return self.cursor.rowcount
        except:
            return None

    def _select(self, *args, where= None, orderBy= False, limitBy= False, 
                distinct= False, groupBy= False, having= False):
        '''Create and return SELECT query.
        fields: one or list of fields to select;
        where: expression for where;
        join: one or list of tables to join, in form Table(join_on_expression);
        tables are taken from fields and `where` expression;
        limitBy: a tuple (start, end).'''
        
        tables = self.getExpressionTables(where) # get tables involved in the query
        fields = []
        joins = []
        for arg in args:
            if orm.isModel(arg):
                fields.extend(arg) # select all table fields
                tables.add(arg)
            elif isinstance(arg, orm.Expression):
                fields.append(arg)
                tables |= self.getExpressionTables(arg)
            elif isinstance(arg, orm.Join):
                joins.append(arg)
            else:
                raise SyntaxError('Uknown argument.')
                
        if not fields: # if not fields specified take them all from the requested tables
            raise SyntaxError('Please indicate at least one field.')
                
        if not tables:
            raise SyntaxError('SELECT: no tables involved.')
        
        sql_f = ', '.join(map(self.render, fields))
        sql_w = ' WHERE ' + self.render(where) if where else ''
        sql_s = ''
        if distinct is True:
            sql_s += 'DISTINCT'
        elif distinct:
            sql_s += 'DISTINCT ON (%s)' % distinct

        if joins: # http://stackoverflow.com/questions/187146/inner-join-outer-join-is-the-order-of-tables-in-from-important
            joinTables = [join.model for join in joins]
            tables = [table for table in tables if table not in joinTables] # remove from tables those which are joined
            sql_t = ', '.join(map(str, tables))
            for join in joins:
                sql_t += ' %s JOIN %s ON %s' % (join.type.upper(), join.model, self.render(join.on))
        else:
            sql_t = ', '.join(map(str, tables))

        sql_o = ''
        if groupBy:
            groupBy = xorify(groupBy)
            sql_o += ' GROUP BY %s' % self.render(groupBy)
            if having:
                sql_o += ' HAVING %s' % having
                
        if orderBy:
            orderBy = orm.listify(orderBy)
            _orderBy = []
            for order in orderBy:
                if isinstance(order, orm.Expression):
                    order = self.render(order) + ' ' + order.sort
                elif isinstance(order, str):
                    if order == '<random>':
                        order = self.RANDOM()
                else:
                    raise SyntaxError('Orderby should receive Field or str.')
                _orderBy.append(order)
            sql_o += ' ORDER BY %s' % ', '.join(_orderBy)
                
        if limitBy:
            if not orderBy and tables:
                sql_o += ' ORDER BY %s' % ', '.join(map(str, (table.id for table in tables)))
                
        return fields, self._selectWithLimit(sql_s, sql_f, sql_t, sql_w, sql_o, limitBy)

    def _selectWithLimit(self, sql_s, sql_f, sql_t, sql_w, sql_o, limitBy):
        if limitBy:
            (lmin, lmax) = limitBy
            sql_o += ' LIMIT %i OFFSET %i' % (lmax - lmin, lmin)
        return 'SELECT %s %s FROM %s%s%s;' % (sql_s, sql_f, sql_t, sql_w, sql_o)

    def select(self, *args, where= None, **attributes):
        fields, sql = self._select(*args, where= where, **attributes)
        self.execute(sql)
        rows = list(self.cursor.fetchall())
        return self.parseResponse(fields, rows)

    def parseResponse(self, fields, rows, blob_decode= True):
        return fields, rows
#        db = self.db
#        virtualtables = []
#        new_rows = []
#        for (i,row) in enumerate(rows):
#            new_row = Row()
#            for j,colname in enumerate(colnames):
#                value = row[j]
#                if not table_field.match(colnames[j]):
#                    if not '_extra' in new_row:
#                        new_row['_extra'] = Row()
#                    new_row['_extra'][colnames[j]] = value
#                    select_as_parser = re.compile("\s+AS\s+(\S+)")
#                    new_column_name = select_as_parser.search(colnames[j])
#                    if not new_column_name is None:
#                        column_name = new_column_name.groups(0)
#                        setattr(new_row,column_name[0],value)
#                    continue
#                (tablename, fieldname) = colname.split('.')
#                table = db[tablename]
#                field = table[fieldname]
#                field_type = field.type
#                if field.type != 'blob' and isinstance(value, str):
#                    try:
#                        value = value.decode(db._db_codec)
#                    except Exception:
#                        pass
#                if isinstance(value, unicode):
#                    value = value.encode('utf-8')
#                if not tablename in new_row:
#                    colset = new_row[tablename] = Row()
#                    if tablename not in virtualtables:
#                        virtualtables.append(tablename)
#                else:
#                    colset = new_row[tablename]
#
#                if isinstance(field_type, SQLCustomType):
#                    colset[fieldname] = field_type.decoder(value)
#                    # field_type = field_type.type
#                elif not isinstance(field_type, str) or value is None:
#                    colset[fieldname] = value
#                elif isinstance(field_type, str) and \
#                        field_type.startswith('reference'):
#                    referee = field_type[10:].strip()
#                    if not '.' in referee:
#                        colset[fieldname] = rid = Reference(value)
#                        (rid._table, rid._record) = (db[referee], None)
#                    else: ### reference not by id
#                        colset[fieldname] = value
#                elif field_type == 'boolean':
#                    if value == True or str(value)[:1].lower() == 't':
#                        colset[fieldname] = True
#                    else:
#                        colset[fieldname] = False
#                elif field_type == 'date' \
#                        and (not isinstance(value, datetime.date)\
#                                 or isinstance(value, datetime.datetime)):
#                    (y, m, d) = map(int, str(value)[:10].strip().split('-'))
#                    colset[fieldname] = datetime.date(y, m, d)
#                elif field_type == 'time' \
#                        and not isinstance(value, datetime.time):
#                    time_items = map(int,str(value)[:8].strip().split(':')[:3])
#                    if len(time_items) == 3:
#                        (h, mi, s) = time_items
#                    else:
#                        (h, mi, s) = time_items + [0]
#                    colset[fieldname] = datetime.time(h, mi, s)
#                elif field_type == 'datetime'\
#                        and not isinstance(value, datetime.datetime):
#                    (y, m, d) = map(int,str(value)[:10].strip().split('-'))
#                    time_items = map(int,str(value)[11:19].strip().split(':')[:3])
#                    if len(time_items) == 3:
#                        (h, mi, s) = time_items
#                    else:
#                        (h, mi, s) = time_items + [0]
#                    colset[fieldname] = datetime.datetime(y, m, d, h, mi, s)
#                elif field_type == 'blob' and blob_decode:
#                    colset[fieldname] = base64.b64decode(str(value))
#                elif field_type.startswith('decimal'):
#                    decimals = int(field_type[8:-1].split(',')[-1])
#                    if self.dbengine == 'sqlite':
#                        value = ('%.' + str(decimals) + 'f') % value
#                    if not isinstance(value, decimal.Decimal):
#                        value = decimal.Decimal(str(value))
#                    colset[fieldname] = value
#                elif field_type.startswith('list:integer'):
#                    if not self.dbengine=='google:datastore':
#                        colset[fieldname] = bar_decode_integer(value)
#                    else:
#                        colset[fieldname] = value
#                elif field_type.startswith('list:reference'):
#                    if not self.dbengine=='google:datastore':
#                        colset[fieldname] = bar_decode_integer(value)
#                    else:
#                        colset[fieldname] = value
#                elif field_type.startswith('list:string'):
#                    if not self.dbengine=='google:datastore':
#                        colset[fieldname] = bar_decode_string(value)
#                    else:
#                        colset[fieldname] = value
#                else:
#                    colset[fieldname] = value
#                if field_type == 'id':
#                    id = colset[field.name]
#                    colset.update_record = lambda _ = (colset, table, id), **a: update_record(_, a)
#                    colset.delete_record = lambda t = table, i = id: t._db(t._id==i).delete()
#                    for (referee_table, referee_name) in \
#                            table._referenced_by:
#                        s = db[referee_table][referee_name]
#                        referee_link = db._referee_name and \
#                            db._referee_name % dict(table=referee_table,field=referee_name)
#                        if referee_link and not referee_link in colset:
#                            colset[referee_link] = Set(db, s == id)
#                    colset['id'] = id
#            new_rows.append(new_row)
#
#        rowsobj = Rows(db, new_rows, colnames, rawrows=rows)
#
#        for tablename in virtualtables:
#            ### new style virtual fields
#            table = db[tablename]
#            fields_virtual = [(f,v) for (f,v) in table.items() if isinstance(v,FieldVirtual)]
#            fields_lazy = [(f,v) for (f,v) in table.items() if isinstance(v,FieldLazy)]
#            if fields_virtual or fields_lazy:
#                for row in rowsobj.records:
#                    box = row[tablename]
#                    for f,v in fields_virtual:
#                        box[f] = v.f(row)
#                    for f,v in fields_lazy:
#                        box[f] = (v.handler or VirtualCommand)(v.f,row)
#
#            ### old style virtual fields
#            for item in table.virtualfields:
#                try:
#                    rowsobj = rowsobj.setvirtualfields(**{tablename:item})
#                except KeyError:
#                    # to avoid breaking virtualfields when partial select
#                    pass
#        return rowsobj
#



class SqliteAdapter(Adapter):
    driver = globals().get('sqlite3')

    def __init__(self, uri, driverArgs= {}):
        self.driverArgs = driverArgs
        #path_encoding = sys.getfilesystemencoding() or locale.getdefaultlocale()[1] or 'utf8'
        dbPath = uri
        if dbPath != ':memory:' and dbPath[0] != '/':
            dbPath = os.path.abspath(os.path.join(os.getcwd(), dbPath))
        self.dbPath = dbPath
        super().__init__(dbPath)

    def connect(self):
        return self.driver.Connection(self.dbPath, **self.driverArgs)

    def _truncate(self, table, mode=''):
        tableName = str(table)
        return ['DELETE FROM %s;' % tableName,
                "DELETE FROM sqlite_sequence WHERE name='%s';" % tableName]

    def lastInsertId(self):
        return self.cursor.lastrowid

    def _getCreateTableIndexes(self, table):
        indexes = []
        for index in table._indexes:
            if index.type != 'primary': # Sqlite has only primary indexes in the CREATE TABLE query
                continue
            indexType = 'PRIMARY KEY'
            columns = []
            for i, field in enumerate(index.fields):
                column = field.column.name
                prefixLength = index.prefixLengths[i] 
                if prefixLength:
                    column += '(%i)' % prefixLength
                sortOrder = index.sortOrders[i]
                column += ' %s' % sortOrder.upper()
                columns.append(column)
                
            indexes.append('%s (%s)' % (indexType, ', '.join(columns)))
            
        return indexes

    def _getCreateTableOther(self, table):
        indexes = []
        for index in table._indexes:
            if index.type == 'primary': # Sqlite has only primary indexes in the CREATE TABLE query
                continue
            elif index.type == 'unique':
                indexType = 'UNIQUE INDEX'
            else:
                indexType = 'INDEX'
            columns = []
            for i, field in enumerate(index.fields):
                column = field.column.name
#                prefixLength = index.prefixLengths[i] 
#                if prefixLength:
#                    column += '(%i)' % prefixLength
                sortOrder = index.sortOrders[i]
                column += ' %s' % sortOrder.upper()
                columns.append(column)
            table = index.fields[0].table
            indexes.append('CREATE %s "%s" ON "%s" (%s)' % (indexType, index.name, table, ', '.join(columns)))
            
        return (';\n' + ';\n'.join(indexes)) if indexes else ''

    def columnInt(self, **kwargs):
        return 'INTEGER'



class MysqlAdapter(Adapter):
    driver = globals().get('mysqldb')
    
    def _getCreateTableOther(self, table):
        return "ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin COMMENT='%s'" % table.__doc__
    
    def RANDOM(self):
        return 'RAND()'

    def lastInsertId(self):
        return self.cursor.insert_id()

    

class Column():
    '''Abstract DB column, supported natively by the DB.'''
    def __init__(self, name, type, field, **kwargs):
        self.name = name
        self.type = type
        self.field = field
        self.props = kwargs # properties 
        


def xorify(orderBy):
    if hasattr(orderBy, '__iter__'):
        return orderBy
    if not orderBy:
        return None
    orderBy2 = orderBy[0]
    for item in orderBy[1:]:
        orderBy2 = orderBy2 | item
    return orderBy2

