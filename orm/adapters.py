"""
This module contains database adapters, which incapsulate all operations specific to a certain database.
All other ORM modules should be database agnostic.
"""
__author__ = "Victor Varvariuc <victor.varvariuc@gmail.com>"

import os, sys, base64
import time, re, math
from datetime import date as Date, datetime as DateTime, timedelta as TimeDelta
from decimal import Decimal
import pprint

import orm
from orm import logger


class Column():
    """Information about database table column.
    """
    def __init__(self, type, name = '', default = None, precision = None, scale = None,
                 unsigned = None, nullable = True, autoincrement = False, comment = ''):
        self.name = name  # db table column name
        self.type = type  # string with the name of data type (decimal, varchar, bigint...)
        self.default = default  # column default value
        self.precision = precision  # char max length or decimal/int max digits
        self.scale = scale  # for decimals
        self.unsigned = unsigned  # for decimals, integers
        # assert nullable or default is not None or autoincrement, 'Column `%s` is not nullable, but has no default value.' % self.name
        self.nullable = nullable  # can contain NULL values?
        self.autoincrement = autoincrement  # for primary integer
        self.comment = comment

    def __str__(self, db = None):
        db = db or GenericAdapter
        assert isinstance(db, GenericAdapter) or \
            (isinstance(db, type) and issubclass(db, GenericAdapter)), \
            'Must be GenericAdapter class or instance'
        colFunc = getattr(db, '_' + self.type.upper())
        columnType = colFunc(self)
        return '%s %s' % (self.name, columnType)

    def str(self):
        attrs = self.__dict__.copy()
        name = attrs.pop('name')
        return '%s(%s)' % (name, ', '.join('%s= %s' % attr for attr in attrs.items()))


class GenericAdapter():
    """Generic DB adapter.
    """
    protocol = 'generic'
    driver = None

    # from this date number of days will be counted when storing DATE values in the DB
    epoch = Date(1970, 1, 1)

    def __init__(self, uri = '', connect = True, autocommit = True):
        """URI is already without protocol."""
        self.uri = uri
        logger.debug('Creating adapter for `%s`' % self)
        self._timings = []
        if connect:
            self.connection = self.connect()
            self.cursor = self.connection.cursor()
        else:
            self.connection = None
            self.cursor = None
        self.autocommit = autocommit

    def __str__(self):
        return "'%s://%s'" % (self.protocol, self.uri)

    def connect(self):
        """Connect to the DB and return the connection. To be overridden in subclasses.
        """
        return None  # DB connection

    def disconnect(self):
        return self.connection.close()

    def commit(self):
        return self.connection.commit()

    def _autocommit(self):
        """Commit if autocommit is set."""
        if self.autocommit:
            self.commit()

    def rollback(self):
        return self.connection.rollback()

    def _execute(self, *a, **b):
        query = a[0]
        logger.debug('DB query: %s' % query)
        t0 = time.time()
        try:
            result = self.cursor.execute(*a, **b)
        except Exception:
            logger.warning(query)
            raise
        self._timings.append((query, round(time.time() - t0, 4)))
        return result

    def execute(self, *args, **kwargs):
        """Execute a query."""
        return self._execute(*args, **kwargs)

    def getLastQuery(self):
        return self._timings[-1]

    @classmethod
    def _FIELD(cls, left):
        """Render a table column name."""
        #db = db or orm.GenericAdapter # we do not use adapter here
        return '%s.%s' % (left.model, left.field.column.name)

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
    def _LIKE(cls, expression, pattern):
        "The LIKE Operator."
        return "(%s LIKE '%s')" % (cls.render(expression), pattern)

    @classmethod
    def _CONCAT(cls, expressions):  # ((expression1) || (expression2) || ...)
        "Concatenate two or more expressions."
        renderedExpressions = []
        for expression in expressions:
            renderedExpressions.append('(' + cls.render(expression) + ')')
        return '(' + ' || '.join(renderedExpressions) + ')'

    @classmethod
    def _IN(cls, first, second):
        if isinstance(second, str):
            return '(%s IN (%s))' % (cls.render(first), second[:-1])
        items = ', '.join(cls.render(item, first) for item in second)
        return '(%s IN (%s))' % (cls.render(first), items)

    @classmethod
    def _COUNT(cls, expression):
        if expression is None:
            return 'COUNT(*)'
        assert isinstance(expression, orm.Expression)
        distinct = getattr(expression, 'distinct', False)
        expression = cls.render(expression)
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
    def _LIMIT(cls, limit = None):
        if not limit:
            return ''
        elif isinstance(limit, int):
            return ' LIMIT %i' % limit
        elif isinstance(limit, (tuple, list)) and len(limit) == 2:
            return ' LIMIT %i OFFSET %i' % (limit[1], limit[0])
        else:
            raise orm.QueryError('limit must be an integer or tuple/list of two elements. Got `%s`'
                                 % limit)

    @classmethod
    def render(cls, value, castField = None):
        """Render of a value (Expression, Field or simple (scalar?) value) in a format suitable for
        operations with castField in the DB.
        @param value:
        @param castField: 
        """
        if isinstance(value, orm.Expression):  # it's an Expression or Field
            if isinstance(value, orm.DateTimeField):
                pass
            return value.__str__(cls)  # render sub-expression
        else:  # it's a value for a DB column
            if value is not None and castField is not None:
                assert isinstance(castField, orm.Expression), 'Cast field must be an Expression.'
                if castField.__class__ is orm.Expression:  # Field - subclass of Expression
                    castField = castField.type  # expression right operand type
                value = castField._cast(value)
                try:
                    return cls._render(value, castField.column)
                except Exception:
                    logger.warning('Check %r._cast().' % castField)
                    raise
            return cls._render(value)

    @classmethod
    def _render(cls, value, column = None):
        """Render a simple value to the format needed for the given column.
        For example, _render a datetime to the format acceptable for datetime columns in this kind
        of DB.
        If there is no column - present the value as string.
        Values are always passed to queries as quoted strings. I.e. even integers like 123 are put
        like '123'.
        """
        if value is None:
            return cls._NULL()
        if column:
            assert isinstance(column, Column), 'It must be a Column instance.'
            encodeFuncName = '_encode' + column.type.upper()
            encodeFunc = getattr(cls, encodeFuncName, None)
            if callable(encodeFunc):
                value = encodeFunc(value, column)
                assert isinstance(value, (str, int, Decimal)), \
                    'Encode `%s.%s` function did not return a string, integer or decimal' \
                    % (cls.__name__, '_encode' + column.type.upper())
                return str(value)
        return cls.escape(value)

    @classmethod
    def escape(cls, value):
        """Convert a value to string, escape single quotes and enclose it in single quotes.
        """
        return "'%s'" % str(value).replace("'", "''")  # escaping single quotes

    @classmethod
    def IntegrityError(cls):
        return cls.driver.IntegrityError

    @classmethod
    def OperationalError(cls):
        return cls.driver.OperationalError

    @classmethod
    def _getCreateTableColumns(cls, table):
        """Get columns declarations for CREATE TABLE statement.
        """
        columns = []
        for field in table:
            column = field.column
            if column is not None:
                columns.append(column.__str__(cls))
        return columns

    @classmethod
    def _getCreateTableIndexes(cls, model):
        """Get indexes declarations for CREATE TABLE statement.
        """
        assert orm.isModel(model)
        indexes = []
        for index in model._indexes:
            if index.type == 'primary':
                indexType = 'PRIMARY KEY'
            elif index.type == 'unique':
                indexType = 'UNIQUE KEY'
            else:
                indexType = 'KEY'
            columns = []
            for indexField in index.indexFields:
                column = indexField.field.name
                if indexField.prefixLength:
                    column += '(%i)' % indexField.prefixLength
                column += ' %s' % indexField.sortOrder.upper()
                columns.append(column)

            indexes.append('%s %s (%s)' % (indexType, index.name, ', '.join(columns)))

        return indexes

    @classmethod
    def _getCreateTableOther(cls, model):
        return []

    @classmethod
    def getCreateTableQuery(cls, model):
        """Get CREATE TABLE statement for the given model in this DB.
        """
        assert orm.isModel(model), 'Provide a Table subclass.'
        columns = cls._getCreateTableColumns(model)
        indexes = cls._getCreateTableIndexes(model)
        query = 'CREATE TABLE %s (' % str(model)
        query += '\n  ' + ',\n  '.join(columns)
        query += ',\n  ' + ',\n  '.join(indexes) + '\n) '
        queries = [query]
        queries.extend(cls._getCreateTableOther(model))
        return queries

    @classmethod
    def _INT(cls, column, intMap = [(1, 'TINYINT'), (2, 'SMALLINT'), (3, 'MEDIUMINT'), (4, 'INT'),
                                    (8, 'BIGINT')]):
        """Render declaration of INT column type.
        `store_rating_sum` BIGINT(20) UNSIGNED NOT NULL DEFAULT '0' COMMENT 'Item\'s rating from store'
        """
        maxInt = int('9' * column.precision)
        # TODO: check for column.unsigned
        bytesCount = math.ceil((maxInt.bit_length() - 1) / 8)  # add one bit for sign
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
        """Encode a value for insertion in a column of INT type.
        """
        return str(int(value))

    @classmethod
    def _CHAR(cls, column):
        """CHAR, VARCHAR
        """
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
        It has a range of 0 to 30 and must be no larger than M.
        """
        return 'DECIMAL(%s, %s)' % (column.precision, column.scale)

    @classmethod
    def _DATE(cls, column):
        return 'DATE'

    @classmethod
    def _DATETIME(cls, column):
        return 'INTEGER'

    @classmethod
    def _encodeDATETIME(cls, value, column):
        """Not all DBs have microsecond precision in DATETIME columns.
        So, generic implementation stores datetimes as integer number of microseconds since the
        Epoch.
        """
        if isinstance(value, str):
            value = DateTime.strptime(value, '%Y-%m-%d %H:%M:%S.%f')
        if isinstance(value, DateTime):
            # in microseconds since the UNIX epoch
            return int(time.mktime(value.timetuple()) * 1000000) + value.microsecond
        raise SyntaxError('Expected datetime.datetime.')

    @classmethod
    def _decodeDATETIME(cls, value, column):
        return DateTime.fromtimestamp(value / 1000000)

    @classmethod
    def _TEXT(cls, column):
        return 'TEXT'

    @classmethod
    def _BLOB(cls, column):
        return 'BLOB'

    @classmethod
    def _encodeBLOB(cls, value, column):
        return "'%s'" % base64.b64encode(value)

    @classmethod
    def _decodeBLOB(cls, value, column):
        return base64.b64decode(value)

#    @classmethod
#    def _getExpressionTables(cls, expression):
#        """Get tables involved in WHERE expression.
#        """
#        tables = set()
#        if orm.isModel(expression):
#            tables.add(expression)
#        elif isinstance(expression, orm.Field):
#            tables.add(expression.table)
#        elif isinstance(expression, orm.Expression):
#            tables |= cls._getExpressionTables(expression.left)
#            tables |= cls._getExpressionTables(expression.right)
#        return tables

    def lastInsertId(self):
        """Last insert ID."""
        return self.cursor.lastrowid

    def _insert(self, *_fields):
        """Get INSERT query.
        INSERT INTO table_name [ ( col_name1, col_name2, ... ) ]
          VALUES ( expression1_1, expression1_2, ... ),
            ( expression2_1, expression2_2, ... ), ... 
        """
        fields = []
        table = None
        for item in _fields:
            assert isinstance(item, (list, tuple)) and len(item) == 2, \
                'Pass tuples with 2 items: (field, value).'
            field, value = item
            assert isinstance(field, orm.Field), 'First item must be a Field.'
            _table = field.table
            table = table or _table
            assert table is _table, 'Pass fields from the same table'
            if not field.column.autoincrement:
                fields.append(item)
        keys = ', '.join(field.column.name for field, value in fields)
        values = ', '.join(self.render(value, field) for field, value in fields)
        return 'INSERT INTO %s (%s) VALUES (%s)' % (table, keys, values)

    def insert(self, *fields):
        """Insert records in the db.
        @param *args: tuples in form (Field, value)
        """
        query = self._insert(*fields)
        self.execute(query)
        self._autocommit()
        return self.lastInsertId()

    def _update(self, *fields, where = None, limit = None):
        """UPDATE table_name SET col_name1 = expression1, col_name2 = expression2, ...
          [ WHERE expression ] [ LIMIT limit_amount ]
          """
        table = None
        for item in fields:
            assert isinstance(item, (list, tuple)) and len(item) == 2, \
                'Pass tuples with 2 items: (field, value).'
            field, value = item
            assert isinstance(field, orm.Field), 'First item in the tuple must be a Field.'
            _table = field.table
            table = table or _table
            assert table is _table, 'Pass fields from the same table'
        sql_w = ' WHERE ' + self.render(where) if where else ''
        sql_v = ', '.join(['%s= %s' % (field.column.name, self.render(value, field))
                           for (field, value) in fields])
        return 'UPDATE %s SET %s%s' % (table, sql_v, sql_w)

    def update(self, *fields, where = None, limit = None):
        """Update records
        @param *args: tuples in form (Field, value)
        @param where: an Expression or string for WHERE part of the DELETE query
        @param limit: a tuple in form (start, end) which specifies the range dor deletion.
        """
        sql = self._update(*fields, where = where)
        self.execute(sql)
        return self.cursor.rowcount

    def _delete(self, table, where, limit = None):
        """DELETE FROM table_name [ WHERE expression ] [ LIMIT limit_amount ]"""
        assert orm.isModel(table)
        sql_w = ' WHERE ' + self.render(where) if where else ''
        return 'DELETE FROM %s%s' % (table, sql_w)

    def delete(self, table, where, limit = None):
        """Delete records from table with the given condition and limit.
        @param talbe: a Model subclass, whose records to delete
        @param where: an Expression or string for WHERE part of the DELETE query
        @param limit: a tuple in form (start, end) which specifies the range dor deletion.
        """
        sql = self._delete(table, where)
        self.execute(sql)
        return self.cursor.rowcount

    def _select(self, *fields, from_ = None, where = None, orderby = False, limit = False,
                distinct = False, groupby = False, having = ''):
        """SELECT [ DISTINCT ] column_expression1, column_expression2, ...
          [ FROM from_clause ]
          [ JOIN table_name ON (join_condition) ]
          [ WHERE where_expression ]
          [ GROUP BY expression1, expression2, ...
              [ HAVING having_expression ] ]
          [ ORDER BY order_column_expr1, order_column_expr2, ... ]
        """
        if not fields:
            raise orm.QueryError('Specify at least on field to select.')

        if not from_:
            from_ = []
            for field in fields:
                if isinstance(field, orm.Expression):
                    # some expressions might have `table` attribute
                    table = getattr(field, 'table', None)
                    if table is not None and table not in from_:
                        from_.append(field.table)

        if not from_:
            raise orm.QueryError('Specify at least one table in `from_` argument or at least on '
                                 'Field to select')

        _fields = []
        for field in fields:
            if isinstance(field, orm.Expression):
                field = self.render(field)
            elif not isinstance(field, str):
                raise orm.QueryError('Field must a Field instance or a string. Got `%s`'
                                     % field.__class__.__name__)
            _fields.append(field)
        sql_fields = ', '.join(_fields)

        tables = []
        joins = []
        texts = []

        for arg in orm.listify(from_):
            if orm.isModel(arg):
                tables.append(str(arg))
            elif isinstance(arg, orm.Join):
                joins.append('%s JOIN %s ON %s' % (arg.type.upper(), arg.model,
                                                   self.render(arg.on)))
            elif isinstance(arg, str):
                texts.append(arg)
            else:
                raise orm.QueryError('`from_` argument should contain only Models, Joins or '
                                     'strings, but got a `%s`' % arg.__class__.__name__)

        sql_from = ''
        if tables:
            sql_from += ' ' + ', '.join(tables)
        if texts:
            sql_from += ' ' + ' '.join(texts)
        if joins:
            sql_from += ' ' + ' '.join(joins)

        if not where:
            sql_where = ''
        elif isinstance(where, dict):
            items = []
            for key, value in where.items():
                items.append('(%s = %s)' % (key, self.render(value)))
            sql_where = ' WHERE ' + ' AND '.join(items)

        elif isinstance(where, str):
            sql_where = ' WHERE ' + where
        elif isinstance(where, orm.Expression):
            sql_where = ' WHERE ' + self.render(where)
        else:
            raise orm.exceptions.QueryError('Where argument should be a dict, str or Expression')

        sql_select = ''
        if distinct is True:
            sql_select += 'DISTINCT'
        elif distinct:
            sql_select += 'DISTINCT ON (%s)' % distinct

        sql_other = ''
        if groupby:
            groupby = xorify(groupby)
            sql_other += ' GROUP BY %s' % self.render(groupby)
            if having:
                sql_other += ' HAVING %s' % having

        if orderby:
            orderby = orm.listify(orderby)
            _orderby = []
            for _order in orderby:
                if isinstance(_order, orm.Expression):
                    _order = self.render(_order) + ' ' + _order.sort
                elif isinstance(_order, str):
                    if _order == '<random>':
                        _order = self.RANDOM()
                else:
                    raise SyntaxError('Orderby should receive Field or str.')
                _orderby.append(_order)
            sql_other += ' ORDER BY %s' % ', '.join(_orderby)

# When using LIMIT, it is a good idea to use an ORDER BY clause that constrains the result rows into a unique order. 
# Otherwise you will get an unpredictable subset of the query's rows -- you may be asking for the tenth through twentieth rows, 
# but tenth through twentieth in what ordering? The ordering is unknown, unless you specified ORDER BY.
#        if limit:
#            if not orderby and tables:
#                sql_other += ' ORDER BY %s' % ', '.join(map(str, (table.id for table in tables)))

        sql_other += self._LIMIT(limit)
        sql = 'SELECT %s %s FROM %s%s%s' % (sql_select, sql_fields, sql_from, sql_where, sql_other)

        return fields, sql

    def select(self, *fields, from_ = None, where = None, **attributes):
        """Create and return SELECT query.
        @param fields: tables, fields or joins;
        @param from_: tables and joined tables to select from.
            None -tables will be automatically extracted from provided fields
            A single table or string
            A list of tables or strings
        @param where: expression for where;
        @param limit: an integer (LIMIT) or tuple/list of two elements (OFFSET, LIMIT)
        @param orderby:
        @param groupby:
        tables are taken from fields and `where` expression;
        """
        fields, query = self._select(*fields, from_ = from_, where = where, **attributes)
        self.execute(query)
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
                    if isinstance(column, orm.Column):
                        decodeFunc = getattr(self, '_decode' + column.type.upper(), None)
                        if callable(decodeFunc):
                            value = decodeFunc(value, column)
                newRow.append(value)
            rows[i] = newRow

        return Rows(self, fields, rows)


####################################################################################################

class Rows():
    """Keeps results of a SELECT and has methods for convenient access.
    """

    def __init__(self, db, fields, rows):
        """
        @param fields: list of queried fields
        @param rows: list of tuples with query result
        """
        self.db = db
        self.fields = tuple(fields)
        self.rows = rows
        self._fieldsStr = tuple(str(field) for field in fields)
        # {field_str: field_order}
        self._fieldsOrder = dict((fieldStr, i) for i, fieldStr in enumerate(self._fieldsStr))

    def value(self, rowNo, field):
        """Get a value
        @param rowNo: row number
        @param field: field instance or column number
        """
        if isinstance(field, int):
            columnNo = field
        else:
            columnNo = self._fieldsOrder[str(field)]
        return self.rows[rowNo][columnNo]

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, i):
        return self.rows[i]

    def __iter__(self):
        """Iterator over records."""
        return iter(self.rows)

    def __str__(self):
        return pprint.pformat(self.rows)

    def dictresult(self):
        """Iterator of the result which return row by row in form 
        {'field1_name': field1_value, 'field2_name': field2_value, ...}
        """
        for row in self.rows:
            yield {self._fieldsStr[i]: value for i, value in enumerate(row)}



####################################################################################################

class SqliteAdapter(GenericAdapter):
    """Adapter for Sqlite databases"""

    protocol = 'sqlite'

    def __init__(self, dbPath, **kwargs):
        self.driverArgs = kwargs
        #path_encoding = sys.getfilesystemencoding() or locale.getdefaultlocale()[1] or 'utf8'
        if dbPath != ':memory:' and not os.path.isabs(dbPath):
            # convert relative path to be absolute
            dbPath = os.path.abspath(os.path.join(os.getcwd(), dbPath))
        self.dbPath = dbPath
        super().__init__(dbPath)

    def connect(self):
        import sqlite3
        self.driver = sqlite3
        dbPath = self.dbPath
        if dbPath != ':memory:' and not os.path.isfile(dbPath):
            raise orm.ConnectionError('"%s" is not a file.\nFor a new database create an empty '
                                      'file.' % dbPath)
        return sqlite3.Connection(self.dbPath, **self.driverArgs)

    def _truncate(self, table, mode = ''):
        tableName = str(table)
        return ['DELETE FROM %s;' % tableName,
                "DELETE FROM sqlite_sequence WHERE name='%s';" % tableName]

    @classmethod
    def _getCreateTableIndexes(cls, model):
        assert orm.isModel(model)
        indexes = []
        for index in model._indexes:
            if index.type != 'primary':  # Sqlite has only primary indexes in the CREATE TABLE query
                continue
            indexType = 'PRIMARY KEY'
            columns = []
            for indexField in index.indexFields:
                column = indexField.field.column.name
                prefixLength = indexField.prefixLength
                if prefixLength:
                    column += '(%i)' % prefixLength
                sortOrder = indexField.sortOrder
                column += ' %s' % sortOrder.upper()
                columns.append(column)

            indexes.append('%s (%s)' % (indexType, ', '.join(columns)))

        return indexes

    @classmethod
    def _getCreateTableOther(cls, model):
        assert orm.isModel(model)
        indexes = []
        for index in model._indexes:
            if index.type == 'primary':  # Sqlite has only primary indexes in the CREATE TABLE query
                continue
            elif index.type == 'unique':
                indexType = 'UNIQUE INDEX'
            else:
                indexType = 'INDEX'
            columns = []
            for indexField in index.indexFields:
                column = indexField.field.column.name
#                prefixLength = index.prefixLengths[i] 
#                if prefixLength:
#                    column += '(%i)' % prefixLength
                sortOrder = indexField.sortOrder
                column += ' %s' % sortOrder.upper()
                columns.append(column)
                # al fields are checked to have the same table, so take the first one
            table = index.indexFields[0].field.table
            indexes.append('CREATE %s "%s" ON "%s" (%s)'
                           % (indexType, index.name, table, ', '.join(columns)))

        return indexes

    @classmethod
    def _CHAR(cls, column):
        return 'TEXT'

    @classmethod
    def _INT(cls, column):
        """INTEGER column type for Sqlite."""
        maxInt = int('9' * column.precision)
        bytesCount = math.ceil((maxInt.bit_length() - 1) / 8)  # add one bit for sign
        if bytesCount > 8:
            raise Exception('Too many digits specified.')
        return 'INTEGER'

    @classmethod
    def _DATE(cls, column):
        """Sqlite db does have native DATE data type.
        We will stores dates in it as integer number of days since the Epoch."""
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
        return cls.epoch + TimeDelta(days = value)

    @classmethod
    def _DECIMAL(cls, column):
        """In Sqlite there is a special DECIMAL, which we won't use.
        We will store decimals as integers."""
        return 'INTEGER'

    @classmethod
    def _encodeDECIMAL(cls, value, column):
        return Decimal(value) * (10 ** column.scale)

    @classmethod
    def _decodeDECIMAL(cls, value, column):
        return Decimal(value) / (10 ** column.scale)

    def getTables(self):
        """Get list of tables (names) in this DB."""
        self.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return [row[0] for row in self.cursor.fetchall()]

    def getColumns(self, tableName):
        """Get columns of a table"""
        self.execute("PRAGMA table_info('%s')" % tableName)  # name, type, notnull, dflt_value, pk
        columns = {}
        for row in self.cursor.fetchall():
            logger.debug('Found table column: %s, %s' % (tableName, row))
            typeName = row[2].lower()
            # INTEGER PRIMARY KEY fields are auto-generated in sqlite
            # INT PRIMARY KEY is not the same as INTEGER PRIMARY KEY!
            autoincrement = bool(typeName == 'integer' and row[5])
            if 'int' in typeName or 'bool' in typeName:  # booleans are sotred as ints in sqlite
                typeName = 'int'
            elif typeName not in ('blob', 'text'):
                raise TypeError('Unexpected data type: %s' % typeName)
            column = Column(type = typeName, field = None, name = row[1], default = row[4],
                            precision = 19, nullable = (not row[3]), autoincrement = autoincrement)
            columns[column.name] = column
            logger.debug('Reproduced table column: %s, %s' % (tableName, column))
        return columns


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
#        _format = "'%% %i.%if'" % (maxDigits + 1, fractionDigits)
#        return _format % Decimal(value)
#
#    def _decodeDECIMAL(self, value, **kwargs):
#        return Decimal(str(value))


####################################################################################################

class MysqlAdapter(GenericAdapter):
    """Adapter for MySql databases."""

    protocol = 'mysql'

    def __init__(self, uri, **kwargs):
        m = re.match('^(?P<user>[^:@]+)(:(?P<password>[^@]*))?@(?P<host>[^:/]+)'
                     '(:(?P<port>[0-9]+))?/(?P<db>[^?]+)$', uri)
        assert m, "Invalid database URI: %s" % self.uri
        kwargs['user'] = m.group('user')
        assert kwargs['user'], 'User required'
        kwargs['passwd'] = m.group('password') or ''
        kwargs['host'] = m.group('host')
        assert kwargs['host'], 'Host name required'
        kwargs['db'] = m.group('db')
        assert kwargs['db'], 'Database name required'
        kwargs['port'] = int(m.group('port') or 3306)
        kwargs['charset'] = 'utf8'
        self.driverArgs = kwargs
        super().__init__(uri)

    def connect(self):
        import pymysql
        self.driver = pymysql
        connection = pymysql.connect(**self.driverArgs)
        connection.execute('SET FOREIGN_KEY_CHECKS=1;')
        connection.execute("SET sql_mode='NO_BACKSLASH_ESCAPES';")
        return connection

    @classmethod
    def _getCreateTableOther(cls, table):
        return ["ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin COMMENT='%s'" % table.__doc__]

    @classmethod
    def _RANDOM(cls):
        return 'RAND()'

    @classmethod
    def _CONCAT(cls, expressions):  # CONCAT(str1,str2,...)
        "Concatenate two or more expressions."
        renderedExpressions = []
        for expression in expressions:
            renderedExpressions.append('(' + cls.render(expression) + ')')
        return 'CONCAT(' + ', '.join(renderedExpressions) + ')'

    def getTables(self):
        """Get list of tables (names) in this DB."""
        self.execute("SHOW TABLES")
        return [row[0] for row in self.cursor.fetchall()]

    def getColumns(self, tableName):
        """Get columns of a table"""
        self.execute("SELECT column_name, data_type, column_default, is_nullable,"
                     "       character_maximum_length, numeric_precision, numeric_scale,"
                     "       column_type, extra, column_comment "
                     "FROM information_schema.columns "
                     "WHERE table_schema = '%s' AND table_name = '%s'"
                     % (self.driverArgs['db'], tableName))
        columns = {}
        for row in self.cursor.fetchall():
            typeName = row[1].lower()
            if 'int' in typeName:
                typeName = 'int'
            elif 'char' in typeName:
                typeName = 'char'
            elif typeName not in ('text', 'datetime', 'date'):
                raise Exception('Unexpected data type: %s' % typeName)
            precision = row[4] or row[5]
            nullable = row[3].lower() == 'yes'
            autoincrement = 'auto_increment' in row[8].lower()
            unsigned = row[7].lower().endswith('unsigned')
            column = Column(type = typeName, field = None, name = row[0], default = row[2],
                            precision = precision, scale = row[6], unsigned = unsigned,
                            nullable = nullable, autoincrement = autoincrement, comment = row[9])
            columns[column.name] = column
        return columns


####################################################################################################

class PostgreSqlAdapter(GenericAdapter):
    """Adapter for PostgreSql databases."""

    protocol = 'postgresql'

    def __init__(self, uri, **kwargs):
        m = re.match('^(?P<user>[^:@]+)(:(?P<password>[^@]*))?@(?P<host>[^:/]+)'
                     '(:(?P<port>[0-9]+))?/(?P<db>[^?]+)$', uri)
        assert m, "Invalid database URI: %s" % self.uri
        kwargs['user'] = m.group('user')
        assert kwargs['user'], 'User required'
        kwargs['password'] = m.group('password') or ''
        kwargs['host'] = m.group('host')
        assert kwargs['host'], 'Host name required'
        kwargs['database'] = m.group('db')
        assert kwargs['database'], 'Database name required'
        kwargs['port'] = int(m.group('port') or 5432)
        self.driverArgs = kwargs
        super().__init__(uri)


    def connect(self):

        import psycopg2
        self.driver = psycopg2
        connection = psycopg2.connect(**self.driverArgs)
        connection.set_client_encoding('UTF8')
#        connection.execute('SET FOREIGN_KEY_CHECKS=1;')
#        connection.execute("SET sql_mode='NO_BACKSLASH_ESCAPES';")
        return connection

    @classmethod
    def _INT(cls, column, intMap = [(2, 'SMALLINT'), (4, 'INTEGER'), (8, 'BIGINT')]):
        """Render declaration of INT column type.
        """
        maxInt = int('9' * column.precision)
        bytesCount = math.ceil((maxInt.bit_length() - 1) / 8)  # add one bit for sign
        for _bytesCount, _columnType in intMap:
            if bytesCount <= _bytesCount:
                break
        else:
            raise Exception('Too big precision specified.')
        columnStr = _columnType

        if column.autoincrement:
            if columnStr == 'BIGINT':
                columnStr = 'BIGSERIAL'
            else:
                columnStr = 'SERIAL'
        else:
            if not column.nullable:
                columnStr += ' NOT'
            columnStr += ' NULL'
            if column.nullable or column.default is not None:
                columnStr += ' DEFAULT ' + cls._render(column.default, None)

        return columnStr

    @classmethod
    def _DATETIME(cls, column):
        return 'timestamp (6) without time zone'

    @classmethod
    def _encodeDATETIME(cls, value, column):
        if isinstance(value, str):
            return DateTime.strptime(value, '%Y-%m-%d %H:%M:%S.%f')
        if isinstance(value, DateTime):
            return value.strftime("'%Y-%m-%d %H:%M:%S.%f'")
        raise SyntaxError('Expected datetime.datetime')

    @classmethod
    def _decodeDATETIME(cls, value, column):
        return value

    @classmethod
    def _getCreateTableIndexes(cls, model):
        assert orm.isModel(model)
        indexes = []
        import ipdb; from pprint import pprint; ipdb.set_trace()
        for index in model._meta.indexes:
            if index.type != 'primary':  # only primary index in the CREATE TABLE query
                continue
            indexType = 'PRIMARY KEY'
            columns = []
            for indexField in index.indexFields:
                column = indexField.field.column.name
                prefixLength = indexField.prefixLength
                if prefixLength:
                    column += '(%i)' % prefixLength
#                sortOrder = indexField.sortOrder
#                column += ' %s' % sortOrder.upper()
                columns.append(column)

            indexes.append('%s (%s)' % (indexType, ', '.join(columns)))

        return indexes

    @classmethod
    def _getCreateTableOther(cls, model):
        assert orm.isModel(model)
        queries = []
        for index in model._indexes:
            if index.type.lower() == 'primary':  # primary index is in the CREATE TABLE query
                continue
            elif index.type.lower() == 'unique':
                indexType = 'UNIQUE'
            else:
                indexType = 'INDEX'
            columns = []
            for indexField in index.indexFields:
                column = indexField.field.column.name
#                prefixLength = index.prefixLengths[i] 
#                if prefixLength:
#                    column += '(%i)' % prefixLength
                sortOrder = indexField.sortOrder
                column += ' %s' % sortOrder.upper()
                columns.append(column)
                # all fields are checked to have the same table, so take the first one
            model = index.indexFields[0].field.model
            queries.append('CREATE %s "%s" ON "%s" (%s)'
                           % (indexType, index.name, model, ', '.join(columns)))

        for field in model:
            column = field.column
            if column is not None and column.comment:
                queries.append(
                    "COMMENT ON COLUMN %s.%s IS %s" % (
                        model._name, column.name, cls.escape(column.comment)
                    )
                )

        return queries

    def getTables(self):
        """Get list of tables (names) in this DB."""
        self.execute("SELECT table_name "
                     "FROM information_schema.tables "
                     "WHERE table_schema = 'public'")
        return [row[0] for row in self.cursor.fetchall()]

    def getColumns(self, tableName):
        """Get columns of a table"""
        rows = self.select(
            'column_name', 'data_type', 'column_default', 'is_nullable', 'character_maximum_length',
            'numeric_precision', 'numeric_scale',
            from_ = 'information_schema.columns',
            where = {'table_schema': 'public', 'table_name': tableName},
        )

        columns = {}
        for row in rows.dictresult():
            typeName = row['data_type'].lower()
            if 'int' in typeName:
                typeName = 'int'
            elif 'char' in typeName:
                typeName = 'char'
            elif typeName == 'timestamp without time zone':
                typeName = 'datetime'
            elif typeName == 'numeric':
                typeName = 'decimal'
            elif typeName not in ('text', 'date'):
                raise Exception('Unexpected data type: `%s`' % typeName)
            precision = row['character_maximum_length'] or row['numeric_precision']
            nullable = row['is_nullable'].lower() == 'yes'
            default = row['column_default']
            if isinstance(default, str) and default.lower().startswith('nextval('):
                autoincrement = True
            else:
                autoincrement = False
            # TODO: retrieve column comment
            column = Column(type = typeName, field = None, name = row['column_name'],
                            default = default,
                            precision = precision, scale = row['numeric_scale'],
                            nullable = nullable, autoincrement = autoincrement)
            columns[column.name] = column
        return columns

    def insert(self, *fields):
        """Overriden to add `RETURNING id`
        """
        query = self._insert(*fields) + ' RETURNING id'
        self.execute(query)
        self._autocommit()
        return self.cursor.fetchone()[0]

    def _dropTable(self, tableName):
        """Return query for dropping a table
        @param table_name: table name or a model describing the table
        """
        if orm.isModel(tableName):
            tableName = tableName._meta.db_name
        elif not isinstance(tableName, str):
            raise AssertionError('Expecting a str or a Model')
        return 'DROP TABLE IF EXISTS %s' % tableName


def xorify(orderBy):
    if hasattr(orderBy, '__iter__'):
        return orderBy
    if not orderBy:
        return None
    orderBy2 = orderBy[0]
    for item in orderBy[1:]:
        orderBy2 = orderBy2 | item
    return orderBy2
