import datetime


def _datify(date: datetime.datetime):
    '''Converts a date-and-time datetime to a date-only datetime'''
    if date.tzinfo is None:
        date = date.replace(tzinfo=datetime.timezone.utc)
    return date.replace(hour=0, minute=0, second=0, microsecond=0)


def _datetimefy(date: datetime.datetime):
    if date.tzinfo is None:
        date = date.replace(tzinfo=datetime.timezone.utc)
    return date.replace(second=0, microsecond=0)


def timestamp_to_date(timestamp: int):
    date = datetime.datetime.fromtimestamp(timestamp)
    return _datify(date)


def date_to_timestamp(date: datetime.datetime):
    if date.tzinfo is None:
        date = date.replace(tzinfo=datetime.timezone.utc)
    date = _datify(date)
    return int(date.timestamp())


def timestamp_to_datetime(timestamp: int):
    date = _datetimefy(datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc))
    return date


def datetime_to_timestamp(date: datetime.datetime):
    if date.tzinfo is None:
        date = date.replace(tzinfo=datetime.timezone.utc)
    date = _datetimefy(date)
    return int(date.timestamp())


def fulldatetime_to_timestamp(date: datetime.datetime):
    '''Returns the timestamp of the date with seconds precision'''
    if date.tzinfo is None:
        date = date.replace(tzinfo=datetime.timezone.utc)
    return int(date.timestamp())


def datetime_now():
    return datetime.datetime.now(tz=datetime.timezone.utc)