import datetime

import dateutil.relativedelta


RelDelta = dateutil.relativedelta.relativedelta
TimeInterval = RelDelta
TimeDelta = datetime.timedelta
Date = datetime.date
DateTime = datetime.datetime


def format(date):
    if date is None:
        return '  .  .    '
    elif isinstance(date, Date):
        return date.strftime('%d.%m.%Y')
    else:
        raise TypeError('Value must a `datetime.date` or `None`.')
