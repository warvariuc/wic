from pprint import pprint

import orm


class Regions(orm.Table):
    region_name = orm.StringField(maxLength= 60)
    region_type_name = orm.StringField(maxLength= 20)

class Locations(orm.Table):
    region_id = orm.RecordIdField(Regions)
    location_name = orm.StringField(maxLength= 100)
    location_type_name = orm.StringField(maxLength= 20)

class Streets(orm.Table):
    location_id = orm.RecordIdField(Locations)
    street_name = orm.StringField(maxLength= 100)
    street_old_name = orm.StringField(maxLength= 100)
    street_type_name = orm.StringField(maxLength= 20)

class Persons(orm.Table):
    last_name = orm.StringField(maxLength= 100)
    first_name = orm.StringField(maxLength= 100)
    middle_name = orm.StringField(maxLength= 100)
    phone_prefix = orm.IntegerField(bytesCount= 2) # phone prefix code of the location
    phone_number = orm.IntegerField(bytesCount= 4)
    location_id = orm.RecordIdField(Locations)
    street_id = orm.RecordIdField(Streets)


ADAPTERS = dict(sqlite= orm.SqliteAdapter, mysql= orm.MysqlAdapter) # available adapters


dbAdapter = orm.connect('sqlite://../mtc.sqlite', ADAPTERS)

#print('\nRegions table fields:')
#for field in Regions:
#    print(' ', field)

# implicit join: get all locations and the regions they are part of
#pprint(dbAdapter.select([], (Regions.id == Locations.region_id), orderBy=[Regions.region_type_name, -Regions.region_name], limitBy=(0, 10)))

# explicit join
pprint(dbAdapter.execute('SELECT persons.*, locations.* FROM persons JOIN locations ON (locations.id = persons.location_id) WHERE (persons.phone_number = 763533) LIMIT 10 OFFSET 0;').fetchall())
print(dbAdapter.getLastQuery(), '\n')

result = dbAdapter.select([Persons, Locations, Regions], 
                          join= [Locations(Locations.id == Persons.location_id, join= 'left'), Regions(Regions.id == Locations.region_id)], 
                          where= Persons.phone_number == '763533', limitBy= (0, 10)) 
pprint(list(zip(result[1], result[0][0])))
print(dbAdapter.getLastQuery(), '\n')

pprint(dbAdapter.execute('SELECT COUNT(*) FROM persons;').fetchall())
print(dbAdapter.getLastQuery(), '\n')

print(dbAdapter.select(orm.COUNT(Persons))) 
print(dbAdapter.getLastQuery(), '\n')

print(dbAdapter.select(orm.COUNT(Persons.street_id))) 
print(dbAdapter.getLastQuery(), '\n')

dbAdapter.insert(Persons.phone_number(222222), Persons.phone_prefix(22))
dbAdapter.commit()
personId = dbAdapter.lastInsertId() 
print(personId)

dbAdapter.update(Persons.phone_number(333333), Persons.phone_prefix(22), where= (Persons.id == personId))
dbAdapter.commit()

dbAdapter.delete(Persons, where= (Persons.id == personId))
dbAdapter.commit()



db = dbAdapter
chunkLength = 100 # how many records to process in one chunk
lastRowId = 0 # last checked item's row_id

def makeRecord(db, table, row, fields):
    _fields = {}
    for i, field in enumerate(fields.values()):
        if isinstance(field, orm.Field) and field.table is table:
            _fields[field.name] = row[i]
    return table.new(db, **_fields)

while True:
    print('Getting next %i records starting with row id %i' % (chunkLength, lastRowId))
    
    rows, fields = db.select(Persons, where= (Persons.id > lastRowId), limitBy= (0, chunkLength))
    if not rows: # walked over the entire table
        break #lastRowId = 0
        
    idIndex = list(fields.values()).index(Persons.id)
    lastRowId = rows[-1][idIndex]
    for i, row in enumerate(rows):
        person = makeRecord(db, Persons, row, fields)
        print(person)
        
        if person.last_name:
            person.last_name = person.last_name.capitalize()
        if person.first_name:
            person.first_name = person.first_name.capitalize()
        if person.middle_name:
            person.middle_name = person.middle_name.capitalize()
            
        db.update(Persons.last_name(person.last_name), 
                  Persons.first_name(person.first_name), 
                  Persons.middle_name(person.middle_name), 
                  where= (Persons.id == person.id))
    db.commit()
