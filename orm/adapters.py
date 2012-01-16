"""Author: Victor Varvariuc <victor.varvariuc@gmail.com"""

"""This module contains database adapters, which incapsulate all operations specific to a certain database.
All other ORM modules should be database agnostic."""

import os, sys, base64
import time, re, math
from datetime import date as Date, datetime as DateTime, timedelta as TimeDelta
from decimal import Decimal
from pprint import pprint

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



class Column():
    """A database table column."""

    def __init__(self, type, field, name='', default=None, precision=None, scale=None, unsigned=None,
                 nullable=True, autoincrement=False, comment=''):
        self.name = name or field.name # column name
        self.type = type # string with the name of data type (decimal, varchar, bigint...)
        self.field = field # model field related to this column
        self.default = default # column default value
        self.precision = precision # char max length or decimal/int max digits
        self.scale = scale # for decimals
        self.unsigned = unsigned # for decimals, integers
        assert nullable or default is not None or autoincrement, 'Column `%s` is not nullable, but has no default value.' % self.name
        self.nullable = nullable # can contain NULL values?
        self.autoincrement = autoincrement # for primary integer
        self.comment = comment

    def __str__(self, db=None):
        db = db or GenericAdapter
        assert isinstance(db, GenericAdapter) or (isinstance(db, type) and issubclass(db, GenericAdapter)), 'Must be GenericAdapter class or instance'
        colFunc = getattr(db, '_' + self.type.upper())
        columnType = colFunc(self)
        return '`%s` %s' % (self.name, columnType)



class Index():
    """A database table index.
    type: index, unique, fulltext, spatial
    sort: asc, desc
    method: btree, hash, gist, and gin"""

    def __init__(self, fields, type='index', name='', sortOrders=None, prefixLengths=None, method='', **kwargs):
        assert isinstance(fields, (list, tuple)), 'Pass a list of indexed fields.'
        assert fields, 'You did not indicate which fields to index.'
        table = fields[0].table
        for field in fields:
            assert isinstance(field, orm.fields.Field)
            assert field.table is table, 'Indexed fields should be from the same table!'
        sortOrders = sortOrders or ['asc'] * len(fields)
        prefixLengths = prefixLengths or [0] * (len(fields))
        assert isinstance(sortOrders, (list, tuple)), 'Sort orders must be a list.'
        assert isinstance(prefixLengths, (list, tuple)), 'Prefix lengths must be a list.'
        assert len(fields) == len(sortOrders) == len(prefixLengths), 'Lists of fields, sort orders and prefix lengths must be the same length.'

        if type == True:
            type = 'index'

        if name == '':
            for field in fields:
                name += field.name + '_'
            name += type
        self.name = name
        self.fields = fields # fields involved in this index
        self.type = type # index type: unique, primary, etc.
        self.prefixLengths = prefixLengths # prefix lengths
        self.sortOrders = sortOrders # sort direction: asc, desc
        self.method = method # if empty - will be used default for this type of DB
        self.other = kwargs # other parameters for a specific DB adapter

    def __str__(self):
        return '{} `{}` ON ({}) {}'.format(self.type, self.name,
                            ', '.join(map(str, self.fields)), self.method)



class GenericAdapter():
    """Generic DB adapter."""

    epoch = Date(1970, 1, 1) # from this date number of days will be counted when storing DATE values in the DB

    def __init__(self, uri='', connect=True, autocommit=True):
        """URI is already without protocol."""
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
        """Connect to the DB and return the connection"""
        return None # DB connection

    def commit(self):
        return self.connection.commit()

    def _autocommit(self):
        """Commit if autocommit is set."""
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
        except Exception:
            print(lastQuery)
            raise
        self._timings.append((lastQuery, round(time.time() - t0, 4)))
        return result

    def execute(self, *args, **kwargs):
        """Execute a query."""
        return self.logExecute(*args, **kwargs)

    def getLastQuery(self):
        return self._timings[-1]

    @classmethod
    def _AND(cls, left, right):
        """Render the AND clause."""
        return '(%s AND %s)' % (cls.render(left), cls.render(right, left))

    @classmethod
    def _OR(cls, left, right):
        """Render the OR clause."""
        return '(%s OR %s)' % (cls.render(left), cls.render(right, left))

    @classmethod
    def _EQ(cls, left, right):
        if right is None:
            return '(%s IS NULL)' % cls.render(left)
        return '(%s = %s)' % (cls.render(left), cls.render(right, left))

    @classmethod
    def _NE(cls, left, right):
        if right is None:
            return '(%s IS NOT NULL)' % cls.render(left)
        return '(%s <> %s)' % (cls.render(left), cls.render(right, left))

    @classmethod
    def _GT(cls, left, right):
        return '(%s > %s)' % (cls.render(left), cls.render(right, left))

    @classmethod
    def _GE(cls, left, right):
        return '(%s >= %s)' % (cls.render(left), cls.render(right, left))

    @classmethod
    def _LT(cls, left, right):
        return '(%s < %s)' % (cls.render(left), cls.render(right, left))

    @classmethod
    def _LE(cls, left, right):
        return '(%s <= %s)' % (cls.render(left), cls.render(right, left))

    @classmethod
    def _ADD(cls, left, right):
        return '(%s + %s)' % (cls.render(left), cls.render(right, left))

    @classmethod
    def _IN(cls, first, second):
        if isinstance(second, str):
            return '(%s IN (%s))' % (cls.render(first), second[:-1])
        items = ', '.join(cls.render(item, first) for item in second)
        return '(%s IN (%s))' % (cls.render(first), items)

    @classmethod
    def _COUNT(cls, expression):
        expression = '*' if orm.isModel(expression) else cls.render(expression)
        distinct = getattr(expression, 'distinct', False)
        if distinct:
            return 'COUNT(DISTINCT %s)' % expression
        else:
            return 'COUNT(%s)' % expression

    @classmethod
    def _MAX(cls, expression):
        return 'MAX(%s)' % cls.render(expression)

    @classmethod
    def _MIN(cls, expression):
        return 'MIN(%s)' % cls.render(expression)

    @classmethod
    def _LOWER(cls, expression):
        return 'LOWER(%s)' % cls.render(expression)

    @classmethod
    def _UPPER(cls, expression):
        return 'UPPER(%s)' % cls.render(expression)

    @classmethod
    def _NULL(cls):
        return 'NULL'

    @classmethod
    def _RANDOM(cls):
        return 'RANDOM()'

    @classmethod
    def render(cls, value, castField=None):
        """Render of a value in a format suitable for operations with this DB field"""
        if isinstance(value, orm.fields.Expression): # it's an expression
            return value._render(cls) # render sub-expression
        else: # it's a value for a DB column
            if value is not None and castField is not None:
                assert isinstance(castField, orm.fields.Expression), 'Cast field must be an Expression.'
                if isinstance(castField, orm.fields.Field): # Field - subclass of Expression
                    pass #
                else: # is the Expression itself
                    castField = castField.type # expression right operand type
                value = castField._cast(value)
                try:
                    return cls._render(value, castField.column)
                except:
                    print('Check %r._cast().' % castField)
                    raise
            return cls._render(value, None)

    @classmethod
    def _render(cls, value, column):
        if value is None:
            return cls._NULL()
        if isinstance(column, Column):
            encodeFunc = getattr(cls, '_encode' + column.type.upper(), None)
            if hasattr(encodeFunc, '__call__'):
                return str(encodeFunc(value, column))
        return "'%s'" % str(value).replace("'", "''") # escaping single quotes  

    @classmethod
    def IntegrityError(cls):
        return cls.driver.IntegrityError

    @classmethod
    def OperationalError(cls):
        return cls.driver.OperationalError

    @classmethod
    def _getCreateTableColumns(cls, table):
        columns = []
        for field in table:
            column = field.column
            if column is not None:
                columns.append(column.__str__(cls))
        return columns

    @classmethod
    def _getCreateTableIndexes(cls, table):
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

    @classmethod
    def _getCreateTableOther(cls, table):
        return ''

    @classmethod
    def getCreateTableQuery(cls, table):
        """Get CREATE TABLE statement for this database"""
        assert orm.isModel(table), 'Provide a Table subclass.'

        columns = cls._getCreateTableColumns(table)
        indexes = cls._getCreateTableIndexes(table)
        other = cls._getCreateTableOther(table)
        query = 'CREATE TABLE %s (' % str(table)
        query += '\n  ' + ',\n  '.join(columns)
        query += ',\n  ' + ',\n  '.join(indexes)
        query += '\n) ' + other + ';'
        return query

    @classmethod
    def _INT(cls, column, intMap=[(1, 'TINYINT'), (2, 'SMALLINT'), (3, 'MEDIUMINT'), (4, 'INT'), (8, 'BIGINT')]):
        """INT column type.
        `store_rating_sum` BIGINT(20) UNSIGNED NOT NULL DEFAULT '0' COMMENT 'Item\'s rating from store'
        """
        maxInt = int('9' * column.precision)
        bytesCount = math.ceil((maxInt.bit_length() - 1) / 8) # add one bit for sign
        for _bytesCount, _columnType in intMap:
            if bytesCount <= _bytesCount:
                break
        else:
            raise Exception('Too big precision specified.')
        columnStr = '%s(%s)' % (_columnType, column.precision)
        if column.unsigned:
            columnStr += ' UNSIGNED'
        if not column.nullable:
            columnStr += ' NOT'
        columnStr += ' NULL'
        if column.nullable or column.default is not None:
            columnStr += ' DEFAULT ' + cls._render(column.default, None)
        if column.autoincrement:
            columnStr += ' AUTO_INCREMENT'
        if column.comment:
            columnStr += ' COMMENT ' + cls._render(column.comment, None)
        return columnStr

    @classmethod
    def _encodeINT(cls, value, column):
        return str(int(value))

    @classmethod
    def _CHAR(cls, column):
        """CHAR, VARCHAR"""
        return 'VARCHAR (%i)' % column.precision

    @classmethod
    def _decodeCHAR(cls, value, column):
        if isinstance(value, bytes):
            return value.decode()
        return str(value)

    @classmethod
    def _DECIMAL(cls, column):
        """The declaration syntax for a DECIMAL column is DECIMAL(M,D). 
        The ranges of values for the arguments in MySQL 5.1 are as follows:
        M is the maximum number of digits (the precision). It has a range of 1 to 65.
        D is the number of digits to the right of the decimal point (the scale). 
        It has a range of 0 to 30 and must be no larger than M."""
        return 'DECIMAL (%s, %s)' % (column.precision, column.scale)

    @classmethod
    def _DATE(cls, column):
        return 'DATE'

    @classmethod
    def _DATETIME(cls, column):
        return 'INTEGER'

    @classmethod
    def _encodeDATETIME(cls, value, column):
        if isinstance(value, str):
            value = DateTime.strptime(value, '%Y-%m-%d %H:%M:%S.%f')
        if isinstance(value, DateTime):
            return int(time.mktime(value.timetuple()) * 1000000) + value.microsecond # in microseconds since the UNIX epoch  
        raise SyntaxError('Expected datetime.datetime.')

    @classmethod
    def _decodeDATETIME(cls, value, column):
        return DateTime.fromtimestamp(value / 1000000)

    @classmethod
    def _encodeBLOB(cls, value, column):
        return "'%s'" % base64.b64encode(value)

    @classmethod
    def getExpressionTables(cls, expression):
        """Get tables involved in WHERE expression."""
        tables = set()
        if orm.isModel(expression):
            tables.add(expression)
        elif isinstance(expression, orm.Field):
            tables.add(expression.table)
        elif isinstance(expression, orm.Expression):
            tables |= cls.getExpressionTables(expression.left)
            tables |= cls.getExpressionTables(expression.right)
        return tables

    def lastInsertId(self):
        """Last insert ID."""

    def _insert(self, *fields):
        """Create and return INSERT query.
        INSERT INTO table_name [ ( col_name1, col_name2, ... ) ]
          VALUES ( expression1_1, expression1_2, ... ),
            ( expression2_1, expression2_2, ... ), ... 
        """
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
        """UPDATE table_name SET col_name1 = expression1, col_name2 = expression2, ...
          [ WHERE expression ] [ LIMIT limit_amount ]"""
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
        return self.cursor.rowcount

    def _delete(self, table, where, limit=None):
        """DELETE FROM table_name [ WHERE expression ] [ LIMIT limit_amount ]"""
        assert orm.isModel(table)
        sql_w = ' WHERE ' + self.render(where) if where else ''
        return 'DELETE FROM %s%s;' % (table, sql_w)

    def delete(self, table, where, limit=None):
        sql = self._delete(table, where)
        self.execute(sql)
        return self.cursor.rowcount

    def _select(self, *args, where=None, orderBy=False, limit=False,
                distinct=False, groupBy=False, having=False):
        """SELECT [ DISTINCT | ALL ] column_expression1, column_expression2, ...
          [ FROM from_clause ]
          [ WHERE where_expression ]
          [ GROUP BY expression1, expression2, ... ]
          [ HAVING having_expression ]
          [ ORDER BY order_column_expr1, order_column_expr2, ... ]
        """
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
                raise ValueError('Uknown argument: %r' % arg)

        assert fields, 'Please indicate at least one field.'
        assert tables, 'SELECT: no tables involved.'

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
                sql_o += ' ORDER BY %s' % ', '.join(map(str, (table.id for table in tables)))

        return fields, self._selectWithLimit(sql_s, sql_f, sql_t, sql_w, sql_o, limit)

    def _selectWithLimit(self, sql_s, sql_f, sql_t, sql_w, sql_o, limit):
        """The syntax may differ in other dbs."""
        if limit:
            (lmin, lmax) = limit
            sql_o += ' LIMIT %i OFFSET %i' % (lmax - lmin, lmin)
        return 'SELECT %s %s FROM %s%s%s;' % (sql_s, sql_f, sql_t, sql_w, sql_o)

    def select(self, *args, where=None, **attributes):
        """Create and return SELECT query.
            @param args: tables, fields or joins;
            @param where: expression for where;
            @param limitBy: a tuple (start, end).
        tables are taken from fields and `where` expression;
        """
        fields, sql = self._select(*args, where=where, **attributes)
        self.execute(sql)
        rows = list(self.cursor.fetchall())
        return self._parseResponse(fields, rows)

    def _parseResponse(self, fields, rows):
        """Post process results fetched from the DB. Return results in Rows object."""
        for i, row in enumerate(rows):
            newRow = []
            for j, field in enumerate(fields):
                value = row[j]
                if value is not None and isinstance(field, orm.Field):
                    column = field.column
                    if isinstance(column, orm.fields.Column):
                        decodeFunc = getattr(self, '_decode' + column.type.upper(), None)
                        if hasattr(decodeFunc, '__call__'):
                            value = decodeFunc(value, column)
                newRow.append(value)
            rows[i] = newRow

        return Rows(self, fields, rows)



class Rows():
    """Keeps results of a SELECT and has methods for convenient access."""

    def __init__(self, db, fields, rows):
        self.db = db
        self.fields = tuple(fields)
        self.rows = rows
        self._fields = dict((str(field), i) for i, field in enumerate(fields)) # {field_str: field_order}

    def value(self, rowNo, field):
        columnNo = self._fields[str(field)]
        return self.rows[rowNo][columnNo]

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, i):
        return self.rows[i]

    def __iter__(self):
        """Iterator over records."""
        return iter(self.rows)





class SqliteAdapter(GenericAdapter):
    driver = globals().get('sqlite3')

    def __init__(self, uri, driverArgs=None):
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

    @classmethod
    def _getCreateTableIndexes(cls, table):
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

    @classmethod
    def _getCreateTableOther(cls, table):
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

    @classmethod
    def _CHAR(cls, column):
        return 'TEXT'

    @classmethod
    def _INT(cls, column):
        """INTEGER column type for Sqlite."""
        print(column.name)
        maxInt = int('9' * column.precision)
        bytesCount = math.ceil((maxInt.bit_length() - 1) / 8) # add one bit for sign
        if bytesCount > 8:
            raise Exception('Too many digits specified.')
        return 'INTEGER'

    @classmethod
    def _DATE(cls, column):
        return 'INTEGER'

    @classmethod
    def _encodeDATE(cls, value, column):
        if isinstance(value, str):
            value = DateTime.strptime(value, '%Y-%m-%d').date()
        if isinstance(value, Date):
            return (value - cls.epoch).days
        raise SyntaxError('Expected "YYYY-MM-DD" or datetime.date.')

    @classmethod
    def _decodeDATE(cls, value, column):
        return cls.epoch + TimeDelta(days=value)

    @classmethod
    def _DECIMAL(cls, column):
        return 'INTEGER'

    @classmethod
    def _encodeDECIMAL(cls, value, column):
        return Decimal(value) * (10 ** column.scale)

    @classmethod
    def _decodeDECIMAL(cls, value, column):
        return Decimal(value) / (10 ** column.scale)

    def getTables(self):
        """"""
#        QStringList QSQLiteDriver::tables(QSql::TableType type) const
#        {
#            QStringList res;
#            if (!isOpen())
#                return res;
#        
#            QSqlQuery q(createResult());
#            q.setForwardOnly(true);
#        
#            QString sql = QLatin1String("SELECT name FROM sqlite_master WHERE %1 "
#                                        "UNION ALL SELECT name FROM sqlite_temp_master WHERE %1");
#            if ((type & QSql::Tables) && (type & QSql::Views))
#                sql = sql.arg(QLatin1String("type='table' OR type='view'"));
#            else if (type & QSql::Tables)
#                sql = sql.arg(QLatin1String("type='table'"));
#            else if (type & QSql::Views)
#                sql = sql.arg(QLatin1String("type='view'"));
#            else
#                sql.clear();
#        
#            if (!sql.isEmpty() && q.exec(sql)) {
#                while(q.next())
#                    res.append(q.value(0).toString());
#            }
#        
#            if (type & QSql::SystemTables) {
#                // there are no internal tables beside this one:
#                res.append(QLatin1String("sqlite_master"));
#            }
#        
#            return res;
#        }

    def getColumns(self, tableName):
        """"""
#        static QSqlIndex qGetTableInfo(QSqlQuery &q, const QString &tableName, bool onlyPIndex = false)
#        {
#            QString schema;
#            QString table(tableName);
#            int indexOfSeparator = tableName.indexOf(QLatin1Char('.'));
#            if (indexOfSeparator > -1) {
#                schema = tableName.left(indexOfSeparator).append(QLatin1Char('.'));
#                table = tableName.mid(indexOfSeparator + 1);
#            }
#            q.exec(QLatin1String("PRAGMA ") + schema + QLatin1String("table_info (") + _q_escapeIdentifier(table) + QLatin1String(")"));
#        
#            QSqlIndex ind;
#            while (q.next()) {
#                bool isPk = q.value(5).toInt();
#                if (onlyPIndex && !isPk)
#                    continue;
#                QString typeName = q.value(2).toString().toLower();
#                QSqlField fld(q.value(1).toString(), qGetColumnType(typeName));
#                if (isPk && (typeName == QLatin1String("integer")))
#                    // INTEGER PRIMARY KEY fields are auto-generated in sqlite
#                    // INT PRIMARY KEY is not the same as INTEGER PRIMARY KEY!
#                    fld.setAutoValue(true);
#                fld.setRequired(q.value(3).toInt() != 0);
#                fld.setDefaultValue(q.value(4));
#                ind.append(fld);
#            }
#            return ind;
#        }


# alternative store format - using strings
#    def _DATE(self, **kwargs):
#        return 'TEXT'
#
#    def _encodeDATE(self, value, **kwargs):
#        if isinstance(value, str):
#            value = self.decodeDATE(value)
#        if isinstance(value, Date):
#            return value.strftime("'%Y-%m-%d'")
#        raise SyntaxError('Expected "YYYY-MM-DD" or datetime.date.')
#
#    def _decodeDATE(self, value, **kwargs):
#        return DateTime.strptime(value, '%Y-%m-%d').date()
#
#    def _DATETIME(self, **kwargs):
#        return 'TEXT'
#
#    def _encodeDATETIME(self, value, **kwargs):
#        if isinstance(value, DateTime):
#            return value.strftime("'%Y-%m-%d %H:%M:%S.%f'")
#        raise SyntaxError('Expected datetime.datetime.')
#    
#    def _decodeDATETIME(self, value, **kwargs):
#        return DateTime.strptime(value, '%Y-%m-%d %H:%M:%S.%f')
#
#    def _DECIMAL(self, **kwargs):
#        return 'TEXT'
#
#    def _encodeDECIMAL(self, value, maxDigits, fractionDigits, **kwargs):
#        _format = "'%% %d.%df'" % (maxDigits + 1, fractionDigits)
#        return _format % Decimal(value)
#
#    def _decodeDECIMAL(self, value, **kwargs):
#        return Decimal(str(value))



class MysqlAdapter(GenericAdapter):
    driver = globals().get('pymysql')

    def __init__(self, uri, driverArgs=None):
        m = re.match('^(?P<user>[^:@]+)(\:(?P<password>[^@]*))?@(?P<host>[^\:/]+)'
                     '(\:(?P<port>[0-9]+))?/(?P<db>[^?]+)$', uri)
        assert m, "Invalid URI: %s" % self.uri
        user = m.group('user')
        assert user, 'User required'
        password = m.group('password') or ''
        host = m.group('host')
        assert host, 'Host name required'
        dbName = m.group('db')
        assert dbName, 'Database name required'
        port = int(m.group('port') or 3306)
        self.driverArgs = driverArgs or {}
        self.driverArgs.update(dict(db=dbName, user=user, passwd=password, host=host, port=port, charset='utf8'))
        super().__init__(uri)
        self.uri = uri
        self.dbName = dbName
        self.execute('SET FOREIGN_KEY_CHECKS=1;')
        self.execute("SET sql_mode='NO_BACKSLASH_ESCAPES';")

    def connect(self):
        return self.driver.connect(**self.driverArgs)

    @classmethod
    def _getCreateTableOther(cls, table):
        return "ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin COMMENT='%s'" % table.__doc__

    @classmethod
    def _RANDOM(cls):
        return 'RAND()'

    def lastInsertId(self):
        return self.cursor.lastrowid

    def getTables(self):
        """Get list of tables (names) in this DB."""
        self.execute("SHOW TABLES")
        return [row[0] for row in self.cursor.fetchall()]

    def getColumns(self, tableName):
        """"""
        self.execute("SELECT column_name, data_type, column_default, is_nullable, character_maximum_length, "
                     "       numeric_precision, numeric_scale, column_type, extra, column_comment "
                     "FROM information_schema.columns "
                     "WHERE table_schema = '%s' AND table_name = '%s'" % (self.dbName, tableName))
        columns = []
        for row in self.cursor.fetchall():
            type = row[1]
            if 'int' in type:
                type = 'int'
            elif 'char' in type:
                type = 'char'
            elif 'text' in type:
                type = 'text'
            elif 'datetime' in type:
                type = 'datetime'
            elif 'date' in type:
                type = 'date'
            else:
                raise Exception('Unexpected data type: %s' % type)
            precision = row[4] or row[5]
            nullable = row[3].upper() == 'YES'
            autoincrement = 'auto_increment' in row[8]
            unsigned = row[7].endswith('unsigned')
            column = Column(type=type, field=None, name=row[0], default=row[2],
                            precision=precision, scale=row[6], unsigned=unsigned,
                            nullable=nullable, autoincrement=autoincrement, comment=row[9])
            columns.append(column)
        return columns




def xorify(orderBy):
    if hasattr(orderBy, '__iter__'):
        return orderBy
    if not orderBy:
        return None
    orderBy2 = orderBy[0]
    for item in orderBy[1:]:
        orderBy2 = orderBy2 | item
    return orderBy2
