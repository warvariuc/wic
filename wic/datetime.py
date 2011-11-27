from datetime import timedelta as TimeDelta, date as Date, datetime as DateTime 
from dateutil.relativedelta import relativedelta as RelDelta


def _format(date):
    if date is None:
        return '  .  .    '
    elif isinstance(date, Date):
        return date.strftime('%d.%m.%Y')
    else:
        raise TypeError('Value must a `datetime.date` or `None`.')
