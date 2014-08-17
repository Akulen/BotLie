from __future__ import division, absolute_import

import six

def total_seconds(td):
    """
    Python 2.7 adds a total_seconds method to timedelta objects.
    See http://docs.python.org/library/datetime.html#datetime.timedelta.total_seconds

    >>> import datetime
    >>> total_seconds(datetime.timedelta(hours=24))
    86400.0
    """
    try:
        result = td.total_seconds()
    except AttributeError:
        seconds = td.seconds + td.days * 24 * 3600
        result = (td.microseconds + seconds * 10**6) / 10**6
    return result


def always_iterable(item):
    """
    Given an object, always return an iterable. If the item is not already
    iterable, return a tuple containing only the item. If item is None, an
    empty iterable is returned.

    >>> always_iterable([1, 2, 3])
    [1, 2, 3]
    >>> always_iterable('foo')
    ('foo',)
    >>> always_iterable(None)
    ()
    >>> always_iterable(range(10))
    range(0, 10)
    >>> def _test_func(): yield "I'm iterable"
    >>> print(next(always_iterable(_test_func())))
    I'm iterable
    """
    if item is None:
        item = ()
    if isinstance(item, six.string_types) or not hasattr(item, '__iter__'):
        item = item,
    return item

