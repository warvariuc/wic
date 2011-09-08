"""
Аналог объекта Справочник 1С
cat = m_catalog ( "Contacts" ) # создание объекта справочника 'Contacts'
cat.find_by_code ( '123' ) # позиционирование на записи с нужным code
print ( cat.name ) # доступ к полю 'name'
""" 

import m_metadata

class m_catalog () :
    def __init__ ( self, catalogName, recordCode ) :
        self.__id = None
        self.name = None
        self.code = None
    def query ( self ) : # query records ( выборка, аналог ВыбратьЭлементы () и ВыбратьЭлементыПоРеквизиту () из 1С )
        pass
    def next ( self ) : # get next record from query ( аналог ПолучитьЭлемент () из 1С )
        pass
    def save ( self ) : # update record in DB
        pass 
    def reload ( self ) : # reload record from DB
        pass
##    def setLock ( flag = None ) : # 
##        if flag != None :
##            pass
##        return lockState

if __name__ == '__main__' :
    person = m_catalog ( 'person', 13975785 )
    person.focus ( 

