'''Author: Victor Varvariuc <victor.varvariuc@gmail.com'''

'''This module contains database adapters, which incapsulate all operations specific to a certain database.
All other ORM modules should be database agnostic.'''

import os, sys, base64
import time, re, math
from datetime import date as Date, datetime as DateTime, timedelta as TimeDelta
from decimal import Decimal

import orm


drivers = []

try:
    import sqlite3
    drivers.append('sqlite3')
except ImportError:
    orm.logger.debug('no sqlite3.dbapi2 driver')

try:
    import pymysql
    drivers.append('pymysql')
except ImportError:
    orm.logger.debug('no pymysql driver')



class GenericAdapter():
    '''Generic DB adapter.'''
    def __init__(self, uri= '', connect= True, autocommit= True):
        '''URI is already without protocol.'''
        print('Creating adapter for "%s"' % uri)
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

    def disconnect(self):
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

    def _AND(self, left, right):
        '''Render the AND clause.'''
        return '(%s AND %s)' % (self.render(left), self.render(right, left))

    def _OR(self, left, right):
        '''Render the OR clause.'''
        return '(%s OR %s)' % (self.render(left), self.render(right, left))
    
    def _EQ(self, left, right):
        if right is None:
            return '(%s IS NULL)' % self.render(left)
        return '(%s = %s)' % (self.render(left), self.render(right, left))

    def _NE(self, left, right):
        if right is None:
            return '(%s IS NOT NULL)' % self.render(left)
        return '(%s <> %s)' % (self.render(left), self.render(right, left))

    def _GT(self, left, right):
        return '(%s > %s)' % (self.render(left), self.render(right, left))

    def _GE(self, left, right):
        return '(%s >= %s)' % (self.render(left), self.render(right, left))

    def _LT(self, left, right):
        return '(%s < %s)' % (self.render(left), self.render(right, left))

    def _LE(self, left, right):
        return '(%s <= %s)' % (self.render(left), self.render(right, left))

    def _ADD(self, left, right):
        return '(%s + %s)' % (self.render(left), self.render(right, left))
    
    def _IN(self, first, second):
        if isinstance(second, str):
            return '(%s IN (%s))' % (self.render(first), second[:-1])
        items = ', '.join(self.render(item, first) for item in second)
        return '(%s IN (%s))' % (self.render(first), items)

    def _COUNT(self, expression):
        expression = '*' if orm.isModel(expression) else self.render(expression)
        distinct = getattr(expression, 'distinct', False)
        if distinct:
            return 'COUNT(DISTINCT %s)' % expression
        else:
            return 'COUNT(%s)' % expression

    def _MAX(self, expression):
        return 'MAX(%s)' % self.render(expression)
    
    def _MIN(self, expression):
        return 'MIN(%s)' % self.render(expression)
    
    def _LOWER(self, expression):
        return 'LOWER(%s)' % self.render(expression)

    def _UPPER(self, expression):
        return 'UPPER(%s)' % self.render(expression)

    
    def render(self, value, castField=None):
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
            return self._NULL()
        if isinstance(column, orm.fields.Column):
            encodeFunc = getattr(self, 'encode' + column.type.upper(), None)
            if hasattr(encodeFunc, '__call__'): 
                return str(encodeFunc(value, column.field))
        return "'%s'" % str(value).replace("'", "''") # escaping single quotes  

    def IntegrityError(self): 
        return self.driver.IntegrityError
    
    def OperationalError(self): 
        return self.driver.OperationalError

    def _getCreateTableColumns(self, table):
        columns = []
        for field in table:
            column = field.column
            if column is not None:
                colFunc = getattr(self, '_' + column.type.upper())
                columnType = colFunc(column.field)
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

    def _NULL(self):   
        return 'NULL'
        
    def _RANDOM(self):
        return 'RANDOM()'

    def _INT(self, field):
        '''INT column type.'''
        maxInt = int('9' * field.maxDigits)
#        bitsCount = len(bin(maxInt)) - 2
#        bytesCount = math.ceil((bitsCount - 1) / 8) # add one bit for sign
        bytesCount = math.ceil((maxInt.bit_length() - 1) / 8) # add one bit for sign

        intMap = [(1, 'TINYINT'), (2, 'SMALLINT'),
                 (3, 'MEDIUMINT'), (4, 'INT'), (8, 'BIGINT')]
        
        for _bytesCount, _columnType in intMap:
            if bytesCount <= _bytesCount:
                if field.autoincrement:
                    _columnType += ' AUTO_INCREMENT'
                return _columnType
        raise Exception('Too many digits specified.')
    
    def encodeINT(self, value, field):
        return str(int(value))

    def _CHAR(self, field):
        '''CHAR, VARCHAR'''
        return 'VARCHAR (%i)' % field.maxLength
            
    def _DECIMAL(self, field):
        '''The declaration syntax for a DECIMAL column is DECIMAL(M,D). 
        The ranges of values for the arguments in MySQL 5.1 are as follows:
        M is the maximum number of digits (the precision). It has a range of 1 to 65.
        D is the number of digits to the right of the decimal point (the scale). 
        It has a range of 0 to 30 and must be no larger than M.'''
        return 'DECIMAL (%s, %s)' % (field.maxDigits, field.fractionDigits)
    
    def encodeBLOB(self, value, field):
        return "'%s'" % base64.b64encode(value)

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
        '''Create and return INSERT query.
        INSERT INTO table_name [ ( col_name1, col_name2, ... ) ]
          VALUES ( expression1_1, expression1_2, ... ),
            ( expression2_1, expression2_2, ... ), ... 
        '''
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
    
    def _update(self, *fields, where=None, limit=None):
        '''UPDATE table_name SET col_name1 = expression1, col_name2 = expression2, ...
          [ WHERE expression ] [ LIMIT limit_amount ]'''
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

    def update(self, *fields, where=None, limit=None):
        sql = self._update(*fields, where=where)
        self.execute(sql)
        try:
            return self.cursor.rowcount
        except Exception:
            return None

    def _delete(self, table, where, limit=None):
        '''DELETE FROM table_name [ WHERE expression ] [ LIMIT limit_amount ]'''
        assert orm.isModel(table)
        sql_w = ' WHERE ' + self.render(where) if where else ''
        return 'DELETE FROM %s%s;' % (table, sql_w)

    def delete(self, table, where, limit=None):
        sql = self._delete(table, where)
        self.execute(sql)
        try:
            return self.cursor.rowcount
        except Exception:
            return None

    def _select(self, *args, where=None, orderBy=False, limit=False,
                distinct=False, groupBy=False, having=False):
        '''SELECT [ DISTINCT | ALL ] column_expression1, column_expression2, ...
          [ FROM from_clause ]
          [ WHERE where_expression ]
          [ GROUP BY expression1, expression2, ... ]
          [ HAVING having_expression ]
          [ ORDER BY order_column_expr1, order_column_expr2, ... ]
        '''        
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
                raise SyntaxError('Uknown argument: %r' % arg)
                
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
                
        if limit:
            if not orderBy and tables:
                sql_o += ' ORDER BY %s' % ', '.join(map(str, (table._id for table in tables)))
                
        return fields, self._selectWithLimit(sql_s, sql_f, sql_t, sql_w, sql_o, limit)

    def _selectWithLimit(self, sql_s, sql_f, sql_t, sql_w, sql_o, limit):
        '''The syntax may differ in other dbs.'''
        if limit:
            (lmin, lmax) = limit
            sql_o += ' LIMIT %i OFFSET %i' % (lmax - lmin, lmin)
        return 'SELECT %s %s FROM %s%s%s;' % (sql_s, sql_f, sql_t, sql_w, sql_o)

    def select(self, *args, where=None, **attributes):
        '''Create and return SELECT query.
        fields: one or list of fields to select;
        where: expression for where;
        join: one or list of tables to join, in form Table(join_on_expression);
        tables are taken from fields and `where` expression;
        limitBy: a tuple (start, end).'''
        fields, sql = self._select(*args, where=where, **attributes)
        self.execute(sql)
        rows = list(self.cursor.fetchall())
        return self.parseResponse(fields, rows)

    def parseResponse(self, fields, rows):
        
        for i in range(len(rows)):
            row = rows[i]
            newRow = []
            for j in range(len(fields)):
                field = fields[j]
                value = row[j]
                if value is not None and isinstance(field, orm.Field):
                    column = field.column
                    if isinstance(column, orm.fields.Column):
                        decodeFunc = getattr(self, 'decode' + column.type.upper(), None)
                        if hasattr(decodeFunc, '__call__'): 
                            value = decodeFunc(value, column.field)
                newRow.append(value)
            rows[i] = newRow
    
        return fields, rows
    


class SqliteAdapter(GenericAdapter):
    driver = globals().get('sqlite3')
    epoch = Date(1970, 1, 1) # from this date number of days will be counted when storing DATE values in the DB

    def __init__(self, uri, driverArgs= None):
        self.driverArgs = driverArgs or {}
        #path_encoding = sys.getfilesystemencoding() or locale.getdefaultlocale()[1] or 'utf8'
        dbPath = uri
        if dbPath != ':memory:' and dbPath[0] != '/':
            dbPath = os.path.abspath(os.path.join(os.getcwd(), dbPath))
        self.dbPath = dbPath
        super().__init__(dbPath)

    def connect(self):
        dbPath = self.dbPath
        if dbPath != ':memory:' and not os.path.isfile(dbPath):
            raise orm.ConnectionError('"%s" is not a file.\nFor a new database create an empty file.' % dbPath)
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
            
        return (';\n\n' + ';\n\n'.join(indexes)) if indexes else ''

    def _CHAR(self, field):
        return 'TEXT'

    def _INT(self, field):
        '''INTEGER column type for Sqlite.'''
        maxInt = int('9' * field.maxDigits)
#        bitsCount = len(bin(maxInt)) - 2
#        bytesCount = math.ceil((bitsCount - 1) / 8) # add one bit for sign
        bytesCount = math.ceil((maxInt.bit_length() - 1) / 8) # add one bit for sign

        if bytesCount > 8:
            raise Exception('Too many digits specified.')
        return 'INTEGER'

    def _DATE(self, field):
        return 'INTEGER'

    def encodeDATE(self, value, field):
        if isinstance(value, str):
            value = DateTime.strptime(value, '%Y-%m-%d').date()
        if isinstance(value, Date):
            return (value - self.epoch).days
        raise SyntaxError('Expected "YYYY-MM-DD" or datetime.date.')

    def decodeDATE(self, value, field):
        return self.epoch + TimeDelta(days= value)

    def _DATETIME(self, field):
        return 'INTEGER'

    def encodeDATETIME(self, value, field):
        if isinstance(value, str):
            value = DateTime.strptime(value, '%Y-%m-%d %H:%M:%S.%f')
        if isinstance(value, DateTime):
            return int(time.mktime(value.timetuple()) * 1000000) + value.microsecond # in microseconds since the UNIX epoch  
        raise SyntaxError('Expected datetime.datetime.')
    
    def decodeDATETIME(self, value, field):
        return DateTime.fromtimestamp(value / 1000000)
    
    def _DECIMAL(self, field):
        return 'INTEGER'

    def encodeDECIMAL(self, value, field):
        return Decimal(value) * (10 ** field.fractionDigits)

    def decodeDECIMAL(self, value, field):
        return Decimal(value) / (10 ** field.fractionDigits)

# alternative store format - using strings
#    def _DATE(self, **kwargs):
#        return 'TEXT'
#
#    def encodeDATE(self, value, **kwargs):
#        if isinstance(value, str):
#            value = self.decodeDATE(value)
#        if isinstance(value, Date):
#            return value.strftime("'%Y-%m-%d'")
#        raise SyntaxError('Expected "YYYY-MM-DD" or datetime.date.')
#
#    def decodeDATE(self, value, **kwargs):
#        return DateTime.strptime(value, '%Y-%m-%d').date()
#
#    def _DATETIME(self, **kwargs):
#        return 'TEXT'
#
#    def encodeDATETIME(self, value, **kwargs):
#        if isinstance(value, DateTime):
#            return value.strftime("'%Y-%m-%d %H:%M:%S.%f'")
#        raise SyntaxError('Expected datetime.datetime.')
#    
#    def decodeDATETIME(self, value, **kwargs):
#        return DateTime.strptime(value, '%Y-%m-%d %H:%M:%S.%f')
#
#    def _DECIMAL(self, **kwargs):
#        return 'TEXT'
#
#    def encodeDECIMAL(self, value, maxDigits, fractionDigits, **kwargs):
#        _format = "'%% %d.%df'" % (maxDigits + 1, fractionDigits)
#        return _format % Decimal(value)
#
#    def decodeDECIMAL(self, value, **kwargs):
#        return Decimal(str(value))



class MysqlAdapter(GenericAdapter):
    driver = globals().get('pymysql')

    def __init__(self, uri, driverArgs= None):
        self.driverArgs = driverArgs or {}
        self.uri = uri
        m = re.match('^(?P<user>[^:@]+)(\:(?P<password>[^@]*))?@(?P<host>[^\:/]+)(\:(?P<port>[0-9]+))?/(?P<db>[^?]+)(\?set_encoding=(?P<charset>\w+))?$', uri)
        if not m:
            raise SyntaxError("Invalid URI: %s" % self.uri)
        user = m.group('user')
        if not user:
            raise SyntaxError('User required')
        password = m.group('password')
        if not password:
            password = ''
        host = m.group('host')
        if not host:
            raise SyntaxError('Host name required')
        db = m.group('db')
        if not db:
            raise SyntaxError('Database name required')
        port = int(m.group('port') or '3306')
        charset = m.group('charset') or 'utf8'
        self.driverArgs.update(dict(db= db, user= user, passwd= password, host= host, port= port, charset= charset))
        super().__init__(uri)
        self.execute('SET FOREIGN_KEY_CHECKS=1;')
        self.execute("SET sql_mode='NO_BACKSLASH_ESCAPES';")
    
    def connect(self):
        return self.driver.connect(**self.driverArgs)

    def _getCreateTableOther(self, table):
        return "ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin COMMENT='%s'" % table.__doc__
    
    def _RANDOM(self):
        return 'RAND()'

    def lastInsertId(self):
        return self.cursor.lastrowid

    



def xorify(orderBy):
    if hasattr(orderBy, '__iter__'):
        return orderBy
    if not orderBy:
        return None
    orderBy2 = orderBy[0]
    for item in orderBy[1:]:
        orderBy2 = orderBy2 | item
    return orderBy2
