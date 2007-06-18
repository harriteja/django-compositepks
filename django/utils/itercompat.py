"""
Providing iterator functions that are not in all version of Python we support.
Where possible, we try to use the system-native version and only fall back to
these implementations if necessary.
"""

import itertools

def compat_tee(iterable):
    """
    Return two independent iterators from a single iterable.

    Based on http://www.python.org/doc/2.3.5/lib/itertools-example.html
    """
    # Note: Using a dictionary and a list as the default arguments here is
    # deliberate and safe in this instance.
    def gen(next, data={}, cnt=[0]):
        dpop = data.pop
        for i in itertools.count():
            if i == cnt[0]:
                item = data[i] = next()
                cnt[0] += 1
            else:
                item = dpop(i)
            yield item
    next = iter(iterable).next
    return gen(next), gen(next)

def groupby(iterable, keyfunc=None):
    """
    Taken from http://docs.python.org/lib/itertools-functions.html
    """
    if keyfunc is None:
        keyfunc = lambda x:x
    iterable = iter(iterable)
    l = [iterable.next()]
    lastkey = keyfunc(l)
    for item in iterable:
        key = keyfunc(item)
        if key != lastkey:
            yield lastkey, l
            lastkey = key
            l = [item]
        else:
            l.append(item)
    yield lastkey, l

if hasattr(itertools, 'tee'):
    tee = itertools.tee
else:
    tee = compat_tee
if hasattr(itertools, 'groupby'):
    groupby = itertools.groupby
