from pprint import pprint

import orm
from orm import Join, LeftJoin


class Regions(orm.Model):
    region_name = orm.StringField(maxLength= 60)
    region_type_name = orm.StringField(maxLength= 20)

class Locations(orm.Model):
    region_id = orm.RecordIdField(Regions)
    location_name = orm.StringField(maxLength= 100)
    location_type_name = orm.StringField(maxLength= 20)

class Streets(orm.Model):
    location_id = orm.RecordIdField(Locations)
    street_name = orm.StringField(maxLength= 100)
    street_old_name = orm.StringField(maxLength= 100)
    street_type_name = orm.StringField(maxLength= 20)

class Persons(orm.Model):
    last_name = orm.StringField(maxLength= 100)
    first_name = orm.StringField(maxLength= 100)
    middle_name = orm.StringField(maxLength= 100)
    phone_prefix = orm.IntegerField(bytesCount= 2) # phone prefix code of the location
    phone_number = orm.IntegerField(bytesCount= 4)
    location_id = orm.RecordIdField(Locations)
    street_id = orm.RecordIdField(Streets)
    
    def checkNames(self):
        '''An item function, like in Django'''
        pass


ADAPTERS = dict(sqlite= orm.SqliteAdapter, mysql= orm.MysqlAdapter) # available adapters


dbAdapter = orm.connect('sqlite://../mtc.sqlite', ADAPTERS)
db = dbAdapter

#print('\nRegions table fields:')
#for field in Regions:
#    print(' ', field)

# implicit join: get all locations and the regions they are part of
#pprint(dbAdapter.select([], (Regions.id == Locations.region_id), orderBy=[Regions.region_type_name, -Regions.region_name], limitBy=(0, 10)))

# explicit join
#pprint(dbAdapter.execute('SELECT persons.*, locations.* FROM persons JOIN locations ON (locations.id = persons.location_id) WHERE (persons.phone_number = 763533) LIMIT 10 OFFSET 0;').fetchall())
#print(dbAdapter.getLastQuery(), '\n')

#result = dbAdapter.select(Persons, Locations, Regions, 
#                          LeftJoin(Locations, Locations.id == Persons.location_id), 
#                          Join(Regions, Regions.id == Locations.region_id), 
#                          where= Persons.phone_number == '763533', 
#                          limitBy= (0, 10))
#pprint(list(zip(result[0], result[1][0])))
#print(dbAdapter.getLastQuery(), '\n')

#pprint(dbAdapter.execute('SELECT COUNT(*) FROM persons;').fetchall())
#print(dbAdapter.getLastQuery(), '\n')
#
#print(dbAdapter.select(orm.COUNT(Persons))) 
#print(dbAdapter.getLastQuery(), '\n')
#
#print(dbAdapter.select(orm.COUNT(Persons.street_id))) 
#print(dbAdapter.getLastQuery(), '\n')

#dbAdapter.insert(Persons.phone_number(222222), Persons.phone_prefix(22))
#dbAdapter.commit()
#personId = dbAdapter.lastInsertId() 
#print(personId)
#
#dbAdapter.update(Persons.phone_number(333333), Persons.phone_prefix(22), where= (Persons.id == personId))
#dbAdapter.commit()
#
#dbAdapter.delete(Persons, where= (Persons.id == personId))
#dbAdapter.commit()

# get last record in Persons table
#pprint(db.select(Persons, orderBy= -Persons.id, limitBy= (0, 1))) 

# get min and max id in Persons table
#pprint(db.select(orm.MIN(Persons.id), orm.MAX(Persons.id)))



#chunkLength = 10000 # how many records to process in one chunk
#lastRowId = 0 # last checked item's row_id
#totalPersonsCount = dbAdapter.select(orm.COUNT(Persons))[0][0][0]
#personsProcessedCount = 0
#
#while True:
#    
#    rows, fields = db.select(Persons, where= (Persons.id > lastRowId), limitBy= (0, chunkLength))
#    if not rows: # walked over the entire table
#        break #lastRowId = 0
#        
#    print('Selected %i records starting with row id %i' % (chunkLength, lastRowId))
#
#    idIndex = list(fields.values()).index(Persons.id)
#    lastRowId = rows[-1][idIndex]
#    for i, row in enumerate(rows):
#        person = makeRecord(db, Persons, row, fields)
#        #print(person)
#        
#        if person.last_name:
#            person.last_name = person.last_name.capitalize()
#        if person.first_name:
#            person.first_name = person.first_name.capitalize()
#        if person.middle_name:
#            person.middle_name = person.middle_name.capitalize()
#            
#        db.update(Persons.last_name(person.last_name), 
#                  Persons.first_name(person.first_name), 
#                  Persons.middle_name(person.middle_name), 
#                  where= (Persons.id == person.id))
#    personsProcessedCount += len(rows)
#    print('Processed %i persons (%.2f %%).' % (personsProcessedCount, personsProcessedCount * 100 / totalPersonsCount))
#    db.commit()

#victor = Persons(first_name= 'Victor', last_name= 'Varvariuc')
#lastRecord = Persons.get(Persons.id == orm.MAX(Persons.id))

#varvariucs = Persons.getList()
#victor.version = Persons.version + 1
#victor.save()
#victor.delete() # delete this existing record
#
person = Persons((Persons.phone_number, 763533), (Persons.phone_prefix, 22), last_name= 'Varvariuc', first_name= 'Victor', db= db)
print(person)
person.save()
print(person.id)
person.first_name = 'Andrei'
person.save()
print(Persons.getOneById(db, 14362421))
pprint(db.select(Persons, where= (Persons.last_name == 'Varvariuc') & (Persons.phone_number == 28072)))
print(Persons.getOne(db, (Persons.last_name == 'Varvariuc') & (Persons.phone_number == 28072)))
Persons.delete(db, Persons.id >= 14362420)
#Persons.delete(where= ()) # delete record from Persons table which fall under the specified WHERE condition
#person.delete()
#Persons.get(where= ()) # delete record from Persons table which fall under the specified WHERE condition
#person.get(where= ()) 
