#author Victor Varvariuc <victor.varvariuc@gmail.com>, 2010,2011
import datetime

class Date():
    """Alternative class for working with dates."""

    __slots__ = ('_date', ) # pre-declaring space for instance attributes and eliminating instance dictionaries

    def __new__(cls, year=0, month=0, day=0): # immutable, so use __new__ not __init__
        self = super().__new__(cls)

        if isinstance(year, Date): # from another Date
            self._date = year.date() if year else None
        elif isinstance(year, datetime.date): # from datetime.date
            self._date = year
        elif isinstance(year, str): # from string 'dd.MM.yyyy'
            try:
                self._date = datetime.datetime.strptime(year, "%d.%m.%Y").date()
            except:
                self._date = None
        else:
            if not (year or month or day):
                self._date = None
            else:
                self._date = datetime.date(int(year), int(month), int(day)) #may raise exception
        return self
    
    def year(self):
        if self:
            return self._date.year
    
    def month(self):
        if self:
            return self._date.month
    
    def day(self):
        if self:
            return self._date.day
    
    def date(self): # return datetime.date object
        if self._date:
            return self._date
        else:
            raise ValueError('Cannot create empty datetime.date.')
        
    def dayOfWeek(self): # Return the day of the week as an integer, where Monday is 0 and Sunday is 6
        if self:
            return self._date.weekday() 
        
    def dayOfYear(self):
        if self:
            return self._date.toordinal() - datetime.date(self.year(), 1, 1).toordinal() + 1
        
    def endOfYear(self):
        if self:
            return Date(self.year(), 12, 31)
        
    def endOfMonth(self):
        if self:
            years, month = divmod(self._date.month, 12)
            return Date(datetime.date(self._date.year + years, month + 1, 1) - datetime.timedelta(1))

        
    def addMonths(self, months):
        if self:
            years, month = divmod(self.month() + months - 1, 12)
            date = Date(self.year() + years, month + 1, 1) # beginning og the month
            return Date(date.year(), date.month(), min(self.day(), date.endOfMonth().day()))
        raise ValueError('Cannot add/subtract from empty date')
        

    @staticmethod
    def today():
        return Date(datetime.date.today())

    @staticmethod
    def fromStr(text, format):
        try:
            return Date(datetime.datetime.strptime(text, format))
        except:
            return Date()
        
    def __format__(self, format_spec): # http://bugs.python.org/issue8913
        return self._date.__format__(format_spec) if self else ''
        
    def __str__(self):
        return self._date.strftime('%d.%m.%Y') if self else '  .  .    '

    def __repr__(self):
        if self:
            return '{}({}, {}, {})'.format(self.__class__.__name__, self._date.year, self._date.month, self._date.day)
        else:
            return '{}()'.format(self.__class__.__name__)

    def __bool__(self): # Return True if self is not empty; otherwise return False
        return True if self._date else False

    def __eq__(self, other): # x==y calls x.__eq__(y)
        if isinstance(other, Date):
#            if not self or not other:
#                return False # if one of dates (or both) is empty they are not equal
            return self._date == other._date
        return NotImplemented

    def __ne__(self, other): # x!=y calls x.__ne__(y)
        return not (self == other)


    def __lt__(self, other): # x<y calls x.__lt__(y)
        if isinstance(other, Date):
            if not self or not other:
                raise ValueError('Cannot compare with empty date')
            return self._date < other._date
        return NotImplemented

    def __le__(self, other): # x<=y calls x.__le__(y)
        if isinstance(other, Date):
            if not self or not other:
                raise ValueError('Cannot compare with empty date')
            return self._date <= other._date
        return NotImplemented

    def __gt__(self, other, context=None): # x>y calls x.__gt__(y)
        if isinstance(other, Date):
            if not self or not other:
                raise ValueError('Cannot compare with empty date')
            return self._date > other._date
        return NotImplemented

    def __ge__(self, other, context=None): # x>=y calls x.__ge__(y)
        if isinstance(other, Date):
            if not self or not other:
                raise ValueError('Cannot compare with empty date')
            return self._date >= other._date
        return NotImplemented

    def __hash__(self): # x.__hash__() <==> hash(x)
        return int(str(self._year) + str(self._month) + str(self._day))

    def __add__(self, days):
        if isinstance(days, int):
            if not self:
                raise ValueError('Cannot add/subtract from empty date')
            return Date(self._date + datetime.timedelta(days))
        return NotImplemented

    __radd__ = __add__
    __iadd__ = __add__

    def __sub__(self, other):
        if isinstance(other, Date):
            if not self or not other:
                raise ValueError('Cannot compare with empty date')
            return (self._date - other._date).days
        elif isinstance(other, int):
            if not self:
                raise ValueError('Cannot add/subtract from empty date')
            return Date(self._date - datetime.timedelta(other))
        return NotImplemented

    __rsub__ = __sub__
    __isub__ = __sub__

    # Support for pickling, copy, and deepcopy
    def __reduce__(self):
        return (self.__class__, (str(self),))

    def __copy__(self):
        if type(self) == Date:
            return self     # I'm immutable; therefore I am my own clone
        return self.__class__(str(self))

    def __deepcopy__(self, memo):
        if type(self) == Date:
            return self     # My components are also immutable
        return self.__class__(str(self))

if __name__ == '__main__': #test
    birthDate = Date(1980, 12, 30) # мне нравятся чётные числа :)
    print('My birth date: ' + str(birthDate) + ', repr: ' + repr(birthDate))
    today = Date.today()
    print('Today is date: ' + str(today))
    print('Today\'s day of the week: ' + str(today.dayOfWeek()))
    print('I am {} days old.'.format(today - birthDate))
    print('2 days back, then 3 days forward: ' + str(today-2+3))
    print('Date 2 months from now: ' + str(today.addMonths(2)))
    date = Date(2012, 2, 5) 
    print('Days in current month: ' + str(today.endOfMonth().day()))
    print('Days in current year: ' + str(today.endOfYear().dayOfYear()))
    print('Empty date: "' + str(Date()) + '", repr: ' + repr(Date()))
    print('Date(1980, 12, 30) == birthDate: ' + str(Date(1980, 12, 30) == birthDate))
    print('Date(1980, 12, 30) != birthDate: ' + str(Date(1980, 12, 30) != birthDate))
    print('Date(1980, 12, 31) == birthDate: ' + str(Date(1980, 12, 31) == birthDate))
    print('%Y/%d/%m: {:%Y/%d/%m}'.format(birthDate))
