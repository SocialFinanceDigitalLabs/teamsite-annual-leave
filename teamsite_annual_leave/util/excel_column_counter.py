from xlsxwriter.utility import xl_col_to_name


class ColumnCounter:
    def __init__(self, start=0):
        self.current = start

    def next(self, count):
        """
        A simple way to set Excel column formats. Prints out the column range for the next `count`
        columns.

        >>> ColumnCounter().next(1)
        'A:A'

        >>> ColumnCounter(start=5).next(1)
        'F:F'

        >>> cc = ColumnCounter()
        >>> cc.next(1)
        'A:A'
        >>> cc.next(5)
        'B:F'
        >>> cc.next(2)
        'G:H'
        >>> cc.next(7)
        'I:O'
        >>> cc.next(30)
        'P:AS'
        >>> cc.next(1)  # Use your harpoons and tow cables to take down an
        'AT:AT'

        :param count: How many columns to include in range
        :return: the Excel range string, e.g. 'A:A'
        """
        start_range = xl_col_to_name(self.current)
        self.current += count
        end_range = xl_col_to_name(self.current - 1)
        return f"{start_range}:{end_range}"
