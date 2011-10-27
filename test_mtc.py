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


ADAPTERS = dict(sqlite=orm.SqliteAdapter, mysql=orm.MysqlAdapter) # available adapters


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
                          where= Persons.phone_number == '763533', limitBy=(0, 10)) 
pprint(list(zip(result[1], result[0][0])))
print(dbAdapter.getLastQuery(), '\n')

pprint(dbAdapter.execute('SELECT COUNT(*) FROM persons;').fetchall())
print(dbAdapter.getLastQuery(), '\n')

print(dbAdapter.select(orm.COUNT(Persons))) 
print(dbAdapter.getLastQuery(), '\n')

print(dbAdapter.select(orm.COUNT(Persons.street_id))) 
print(dbAdapter.getLastQuery(), '\n')

#print(dbAdapter._insert(Persons.first_name('First name'), Persons.last_name('Last name'), Persons.location_id(2)))
print(dbAdapter.insert(Persons.phone_number(222222), Persons.phone_prefix(22)))
print(dbAdapter.lastInsertId())
dbAdapter.commit()

#print(dbAdapter.select([], Locations.id == Persons.location_id, limitBy=(0, 10)))

#pprint(dbAdapter.select(list(Persons) + list(Locations), (Locations.id == Persons.location_id) & (Persons.phone_number == '763533'), limitBy=(0, 10)))
#print(dbAdapter.getLastQuery())
