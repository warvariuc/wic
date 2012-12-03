from pprint import pprint

import orm
from orm import Join, LeftJoin


class Region(orm.Model):
    region_name = orm.CharField(max_length=60)
    region_type_name = orm.CharField(max_length=20)


class Location(orm.Model):
    region = orm.RelatedRecordField(Region)
    location_name = orm.CharField(max_length=100)
    location_type_name = orm.CharField(max_length=20)


class Street(orm.Model):
    location = orm.RelatedRecordField(Location)
    street_name = orm.CharField(max_length=100)
    street_old_name = orm.CharField(max_length=100)
    street_type_name = orm.CharField(max_length=20)


class Person(orm.Model):
    last_name = orm.CharField(max_length=100)
    first_name = orm.CharField(max_length=100)
    middle_name = orm.CharField(max_length=100)
    phone_prefix = orm.IntegerField(max_digits=3) # phone prefix code of the location
    phone_number = orm.IntegerField(max_digits=10)
    location = orm.RelatedRecordField(Location)
    street = orm.RelatedRecordField(Street)

    def check_names(self):
        """An item function, like in Django"""
        pass


db = orm.connect('sqlite://papp/databases/mtc.sqlite')

#print('\nRegions table fields:')
#for field in Regions:
#    print(' ', field)

# implicit join: get all locations and the regions they are part of
#pprint(dbAdapter.select([], (Regions.id == Locations.region_id), orderBy=[Regions.region_type_name, -Regions.region_name], limitBy=(0, 10)))

# explicit join
#pprint(dbAdapter.execute('SELECT persons.*, locations.* FROM persons JOIN locations ON (locations.id = persons.location_id) WHERE (persons.phone_number = 763533) LIMIT 10 OFFSET 0;').fetchall())
#print(dbAdapter.get_last_query(), '\n')

rows = db.select(
    Person.last_name, Person.first_name, Location.location_name, Region.region_name,
    from_=[Person, LeftJoin(Location, Location.id == Person.location),
    Join(Region, Region.id == Location.region)],
    where=Person.phone_number == '763533',
    limit=10
)
pprint(list(zip(rows.fields, rows)))
print(db.get_last_query(), '\n')

#pprint(dbAdapter.execute('SELECT COUNT(*) FROM persons;').fetchall())
#print(dbAdapter.get_last_query(), '\n')
#
#print(dbAdapter.select(orm.COUNT(Persons))) 
#print(dbAdapter.get_last_query(), '\n')
#
#print(dbAdapter.select(orm.COUNT(Persons.street_id))) 
#print(dbAdapter.get_last_query(), '\n')

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
#totalPersonsCount = dbAdapter.select(orm.COUNT(Persons))[1][0][0]
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


#person = Persons((Persons.phone_number, 763533), (Persons.phone_prefix, 22), last_name= 'Varvariuc', first_name= 'Victor', db= db)
#print(person)
#person.save()
#print(person.id)
#person.first_name = 'Andrei'
#person.save()
#print(Persons.get_one(db, id = 14362421))
#pprint(db.select(Persons, where= (Persons.last_name == 'Varvariuc') & (Persons.phone_number == 28072)))
#print(Persons.get_one(db, (Persons.last_name == 'Varvariuc') & (Persons.phone_number == 28072)))
#Persons.delete(db, Persons.id >= 14362420)

#pprint(db._update(Persons.phone_prefix(Persons.phone_prefix + 1), where= (Persons.id == 1))) # UPDATE persons SET phone_prefix= (persons.phone_prefix + 1) WHERE (persons.id = 1); 

#for person in Persons.get(db, (Persons.last_name == 'Varvariuc') & (Persons.phone_prefix == 236)):
#    print(str(person), str(Locations.get_one(db, id = person.location_id)))
pprint(list(db.select(*Person, where=(orm.UPPER(Person.last_name) == 'VARVARIUC'), limit=5)))
print(db.get_last_query(), '\n')
