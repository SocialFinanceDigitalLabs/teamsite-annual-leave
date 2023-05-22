from datetime import timedelta


def daterange(start, end):
    """A generator for ranges but unlike normal python generators is is inclusive"""
    current = start
    while current <= end:
        type = [current == start, current == end]
        yield current, type
        current = current + timedelta(days=1)
