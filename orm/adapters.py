'''This module contains database adapters, which incapsulate all operations specific to a certain database.
All other ORM modules should be database agnostic.'''

import base64
import time, inspect
from collections import OrderedDict
import orm


drivers = []

try:
    from sqlite3 import dbapi2 as sqlite3
    drivers.append('SQLite3')
except ImportError:
    orm.logger.debug('no sqlite3.dbapi2 driver')



class Adapter():
    '''Generic DB adapter.'''
    def __init__(self, uri='', connect=True):
        '''URI is already without protocol.'''
        print(uri)
        if connect:
            self.connection = self.connect()
        else:
            self.connection = None
    
    def connect(self):
        '''Connect to the DB and return the connection'''
        return None # DB connection

    def logExecute(self, *a, **b):
        lastsql = a[0]
        t0 = time.time()
        ret = self.cursor.execute(*a, **b)
        self.db._timings.append((lastsql, time.time() - t0))
        return ret
    
    def getLastSql(self):
        return self.db._timings[-1][0]

    def execute(self, *a, **b):
        return self.logExecute(*a, **b)

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
    
    def render(self, value, castField=None):
        '''Render of a value in a format suitable for operations with this DB field'''
        if isinstance(value, orm.fields.Expression): # it's an expression
            return value._render(self) # render sub-expression
        else: # it's a value for a DB column
            if value is not None and castField is not None:
                assert isinstance(castField, orm.fields.Expression)
                if isinstance(castField, orm.fields.Field): # Field - subclass of Expression
                    pass # TODO: JOIN
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
        renderFunc = getattr(self, 'render' + column.type.capitalize(), None)
        if hasattr(renderFunc, '__call__'): 
            return renderFunc(value)
        return str(value)  

#            elif isinstance(dbType, DbIntegerField):
#                if isinstance(obj, (datetime.date, datetime.datetime)):
#                    obj = obj.isoformat()[:10]
#                else:
#                    obj = str(obj)
#            elif fieldtype == 'datetime':
#                if isinstance(obj, datetime.datetime):
#                    obj = obj.isoformat()[:19].replace('T', ' ')
#                elif isinstance(obj, datetime.date):
#                    obj = obj.isoformat()[:10] + ' 00:00:00'
#                else:
#                    obj = str(obj)
#            elif fieldtype == 'time':
#                if isinstance(obj, datetime.time):
#                    obj = obj.isoformat()[:10]
#                else:
#                    obj = str(obj)
#            if not isinstance(obj, str):
#                obj = str(obj)
        
             
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
        assert inspect.isclass(table) and issubclass(table, orm.Table)
        
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

    def typeInt(self, bytesCount=4, intMap = [(1, 'TINYINT'), (2, 'SMALLINT'), 
                    (3, 'MEDIUMINT'), (4, 'INT'), (8, 'BIGINT')], autoincrement=False, **kwargs):
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

    def renderBlob(self, value):
        return base64.b64encode(str(value))
    
    def typeDecimal(self, maxDigits, decimalPlaces=0, **kwargs):
        '''The declaration syntax for a DECIMAL column is DECIMAL(M,D). The ranges of values for the arguments in MySQL 5.1 are as follows:
        M is the maximum number of digits (the precision). It has a range of 1 to 65. (Older versions of MySQL permitted a range of 1 to 254.)
        D is the number of digits to the right of the decimal point (the scale). It has a range of 0 to 30 and must be no larger than M.'''
        return 'DECIMAL (%s, %s)' % (maxDigits, decimalPlaces)
    
    def typeChar(self, maxLength, lengthFixed=False, **kwargs):
        '''CHAR, VARCHAR'''
        if lengthFixed:
            return 'CHAR(%i)' % maxLength
        else:
            return 'VARCHAR(%i)' % maxLength
            

    def _select(self, where, fields=None, orderby=False, limitby=False, join=False, distinct=False, groupby=False, 
                having=False, left=False):
        fields = fields or []
        tables = self.getExpressionTables(where) # get tables involved in the query
        #where = self.filter_tenant(where, tablenames) # process the query ???
        if not fields: # if not fields specified take them all from the requested tables
            for table in tables:
                for field in table:
                    fields.append(field)
        else:
            for field in fields:
                assert isinstance(field, orm.Field)
#                if isinstance(field, str) and table_field.match(field):
#                    tn, fn = field.split('.')
#                    field = self.db[tn][fn]
                tables |= self.getExpressionTables(field)
        if not tables:
            raise SyntaxError('SELECT: no tables involved.')
        columns = OrderedDict(zip(map(self.render, fields), fields))
        sql_f = ', '.join(columns)
        if where:
            sql_w = ' WHERE ' + self.render(where)
        else:
            sql_w = ''
        sql_o = ''
        sql_s = ''
        if distinct is True:
            sql_s += 'DISTINCT'
        elif distinct:
            sql_s += 'DISTINCT ON (%s)' % distinct
#        inner_join = join
#        if inner_join:
#            icommand = self.JOIN()
#            if not isinstance(inner_join, (tuple, list)):
#                inner_join = [inner_join]
#            ijoint = [t._tablename for t in inner_join if not isinstance(t, orm.Expression)]
#            ijoinon = [t for t in inner_join if isinstance(t, orm.Expression)]
#            ijoinont = [t.first._tablename for t in ijoinon]
#            iexcluded = [t for t in tablenames if not t in ijoint + ijoinont]
#        if left:
#            join = left
#            command = self.LEFT_JOIN()
#            if not isinstance(join, (tuple, list)):
#                join = [join]
#            joint = [t._tablename for t in join if not isinstance(t, orm.Expression)]
#            joinon = [t for t in join if isinstance(t, orm.Expression)]
#            #patch join+left patch (solves problem with ordering in left joins)
#            tables_to_merge = {}
#            [tables_to_merge.update(dict.fromkeys(self.tables(t))) for t in joinon]
#            joinont = [t.first._tablename for t in joinon]
#            [tables_to_merge.pop(t) for t in joinont if t in tables_to_merge]
#            important_tablenames = joint + joinont + tables_to_merge.keys()
#            excluded = [t for t in tablenames if not t in important_tablenames ]
#        def alias(t):
#            return str(self.db[t])
#        if inner_join and not left:
#            sql_t = ', '.join(alias(t) for t in iexcluded)
#            for t in ijoinon:
#                sql_t += ' %s %s' % (icommand, str(t))
#        elif not inner_join and left:
#            sql_t = ', '.join([alias(t) for t in excluded + tables_to_merge.keys()])
#            if joint:
#                sql_t += ' %s %s' % (command, ','.join([t for t in joint]))
#            for t in joinon:
#                sql_t += ' %s %s' % (command, str(t))
#        elif inner_join and left:
#            sql_t = ','.join([alias(t) for t in excluded + \
#                                  tables_to_merge.keys() if t in iexcluded ])
#            for t in ijoinon:
#                sql_t += ' %s %s' % (icommand, str(t))
#            if joint:
#                sql_t += ' %s %s' % (command, ','.join([t for t in joint]))
#            for t in joinon:
#                sql_t += ' %s %s' % (command, str(t))
#        else:
#            sql_t = ', '.join(alias(t) for t in tablenames)
        sql_t = ', '.join(map(str, tables))
        if groupby:
            groupby = xorify(groupby)
            sql_o += ' GROUP BY %s' % self.render(groupby)
            if having:
                sql_o += ' HAVING %s' % having
        if orderby:
            orderby = xorify(orderby)
            if str(orderby) == '<random>':
                sql_o += ' ORDER BY %s' % self.RANDOM()
            else:
                sql_o += ' ORDER BY %s' % self.render(orderby)
        if limitby:
            if not orderby and tables:
                sql_o += ' ORDER BY %s' % ', '.join(map(str, (table.id for table in tables)))
        return self.select_limitby(sql_s, sql_f, sql_t, sql_w, sql_o, limitby), columns

    def select_limitby(self, sql_s, sql_f, sql_t, sql_w, sql_o, limitby):
        if limitby:
            (lmin, lmax) = limitby
            sql_o += ' LIMIT %i OFFSET %i' % (lmax - lmin, lmin)
        return 'SELECT %s %s FROM %s%s%s;' % (sql_s, sql_f, sql_t, sql_w, sql_o)

    def select(self, where, fields, *attributes):
        sql, columns = self._select(where, fields, *attributes)
        self.execute(sql)
        rows = list(self.cursor.fetchall())
        limitby = attributes.get('limitby', (0,))
        rows = self.rowslice(rows, limitby[0], None)
        return self.parse(rows, self._colnames)

    def parseResponse(self, rows, columns, blob_decode=True):
        db = self.db
        virtualtables = []
        new_rows = []
        for (i, row) in enumerate(rows):
            new_row = Row()
            for j, colname in enumerate(columns):
                value = row[j]
                if not table_field.match(colnames[j]):
                    if not '_extra' in new_row:
                        new_row['_extra'] = Row()
                    new_row['_extra'][colnames[j]] = value
                    select_as_parser = re.compile("\s+AS\s+(\S+)")
                    new_column_name = select_as_parser.search(colnames[j])
                    if new_column_name is not None:
                        column_name = new_column_name.groups(0)
                        setattr(new_row, column_name[0], value)
                    continue
                (tablename, fieldname) = colname.split('.')
                table = db[tablename]
                field = table[fieldname]
                field_type = field.type
                if field.type != 'blob' and isinstance(value, str):
                    try:
                        value = value.decode(db._db_codec)
                    except Exception:
                        pass
                if isinstance(value, unicode):
                    value = value.encode('utf-8')
                if not tablename in new_row:
                    colset = new_row[tablename] = Row()
                    if tablename not in virtualtables:
                        virtualtables.append(tablename)
                else:
                    colset = new_row[tablename]

                if isinstance(field_type, SQLCustomType):
                    colset[fieldname] = field_type.decoder(value)
                    # field_type = field_type.type
                elif not isinstance(field_type, str) or value is None:
                    colset[fieldname] = value
                elif isinstance(field_type, str) and \
                        field_type.startswith('reference'):
                    referee = field_type[10:].strip()
                    if not '.' in referee:
                        colset[fieldname] = rid = Reference(value)
                        (rid._table, rid._record) = (db[referee], None)
                    else: ### reference not by id
                        colset[fieldname] = value
                elif field_type == 'boolean':
                    if value == True or str(value)[:1].lower() == 't':
                        colset[fieldname] = True
                    else:
                        colset[fieldname] = False
                elif field_type == 'date' \
                        and (not isinstance(value, datetime.date)\
                                 or isinstance(value, datetime.datetime)):
                    (y, m, d) = map(int, str(value)[:10].strip().split('-'))
                    colset[fieldname] = datetime.date(y, m, d)
                elif field_type == 'time' \
                        and not isinstance(value, datetime.time):
                    time_items = map(int, str(value)[:8].strip().split(':')[:3])
                    if len(time_items) == 3:
                        (h, mi, s) = time_items
                    else:
                        (h, mi, s) = time_items + [0]
                    colset[fieldname] = datetime.time(h, mi, s)
                elif field_type == 'datetime'\
                        and not isinstance(value, datetime.datetime):
                    (y, m, d) = map(int, str(value)[:10].strip().split('-'))
                    time_items = map(int, str(value)[11:19].strip().split(':')[:3])
                    if len(time_items) == 3:
                        (h, mi, s) = time_items
                    else:
                        (h, mi, s) = time_items + [0]
                    colset[fieldname] = datetime.datetime(y, m, d, h, mi, s)
                elif field_type == 'blob' and blob_decode:
                    colset[fieldname] = base64.b64decode(str(value))
                elif field_type.startswith('decimal'):
                    decimals = int(field_type[8:-1].split(',')[-1])
                    if self.dbengine == 'sqlite':
                        value = ('%.' + str(decimals) + 'f') % value
                    if not isinstance(value, decimal.Decimal):
                        value = decimal.Decimal(str(value))
                    colset[fieldname] = value
                elif field_type.startswith('list:integer'):
                    if not self.dbengine == 'google:datastore':
                        colset[fieldname] = bar_decode_integer(value)
                    else:
                        colset[fieldname] = value
                elif field_type.startswith('list:reference'):
                    if not self.dbengine == 'google:datastore':
                        colset[fieldname] = bar_decode_integer(value)
                    else:
                        colset[fieldname] = value
                elif field_type.startswith('list:string'):
                    if not self.dbengine == 'google:datastore':
                        colset[fieldname] = bar_decode_string(value)
                    else:
                        colset[fieldname] = value
                else:
                    colset[fieldname] = value
                if field_type == 'id':
                    id = colset[field.name]
                    colset.update_record = lambda _ = (colset, table, id), **a: update_record(_, a)
                    colset.delete_record = lambda t = table, i = id: t._db(t._id == i).delete()
                    for (referee_table, referee_name) in \
                            table._referenced_by:
                        s = db[referee_table][referee_name]
                        referee_link = db._referee_name and \
                            db._referee_name % dict(table=referee_table, field=referee_name)
                        if referee_link and not referee_link in colset:
                            colset[referee_link] = Set(db, s == id)
                    colset['id'] = id
            new_rows.append(new_row)

        rowsobj = Rows(db, new_rows, colnames, rawrows=rows)

        for tablename in virtualtables:
            ### new style virtual fields
            table = db[tablename]
            fields_virtual = [(f, v) for (f, v) in table.items() if isinstance(v, FieldVirtual)]
            fields_lazy = [(f, v) for (f, v) in table.items() if isinstance(v, FieldLazy)]
            if fields_virtual or fields_lazy:
                for row in rowsobj.records:
                    box = row[tablename]
                    for f, v in fields_virtual:
                        box[f] = v.f(row)
                    for f, v in fields_lazy:
                        box[f] = (v.handler or VirtualCommand)(v.f, row)

            ### old style virtual fields
            for item in table.virtualfields:
                try:
                    rowsobj = rowsobj.setvirtualfields(**{tablename:item})
                except KeyError:
                    # to avoid breaking virtualfields when partial select
                    pass
        return rowsobj

    def _count(self, where, distinct=None):
        tablenames = map(str, self.getExpressionTables(where))
        if where:
            sql_w = ' WHERE ' + self.render(where)
        else:
            sql_w = ''
        sql_t = ','.join(tablenames)
        if distinct:
            if isinstance(distinct, (list, tuple)):
                distinct = xorify(distinct)
            sql_d = self.render(distinct)
            return 'SELECT COUNT(DISTINCT %s) FROM %s%s;' % (sql_d, sql_t, sql_w)
        return 'SELECT COUNT(*) FROM %s%s;' % (sql_t, sql_w)

    def count(self, query, distinct=None):
        self.execute(self._count(query, distinct))
        return self.cursor.fetchone()[0]


    def getExpressionTables(self, expression):
        '''Get tables involved in WHERE expression.'''
        tables = set()
        if isinstance(expression, orm.Field):
            tables.add(expression.table)
        elif isinstance(expression, orm.Expression):
            tables |= self.getExpressionTables(expression.left)
            tables |= self.getExpressionTables(expression.right)
        return tables



class SqliteAdapter(Adapter):
    driver = globals().get('sqlite3')

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
            indexes.append('CREATE %s "%s" ON "%s" (%s)' % (indexType, index.name, str(table), ', '.join(columns)))
            
        return (';\n' + ';\n'.join(indexes)) if indexes else ''

    def columnInt(self, **kwargs):
        return 'INTEGER'



class MysqlAdapter(Adapter):
    driver = globals().get('mysqldb')
    
    def _getCreateTableOther(self, table):
        return "ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin COMMENT='%s'" % table.__doc__
    
    def RANDOM(self):
        return 'RAND()'
    

class Column():
    '''Abstract DB column, supported natively by the DB.'''
    def __init__(self, name, type, field, **kwargs):
        self.name = name
        self.type = type
        self.field = field
        self.props = kwargs # properties 
        


def xorify(orderBy):
    if not isinstance(orderBy, (list, tuple)):
        return orderBy
    if not orderBy:
        return None
    orderBy2 = orderBy[0]
    for item in orderBy[1:]:
        orderBy2 = orderBy2 | item
    return orderBy2

