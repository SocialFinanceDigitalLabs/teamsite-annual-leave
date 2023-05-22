from datetime import date

from django.test import TestCase

from team_annual_leave.util.bank_holiday_parser import parse_bank_holiday_def


class ParseBankHolidaysTest(TestCase):
    fixtures = ["record-types"]

    def test_parse_single_date(self):
        rec = parse_bank_holiday_def("2020-01-01 - Public Holiday - New Year’s Day")

        self.assertEqual(rec.start_date, date.fromisoformat("2020-01-01"))
        self.assertEqual(rec.end_date, date.fromisoformat("2020-01-01"))
        self.assertEqual(rec.record_type.title, "Public Holiday")
        self.assertEqual(rec.title, "New Year’s Day")
        self.assertEqual(rec.year, 2020)

    def test_parse_multi_date(self):
        rec = parse_bank_holiday_def(
            "2020-12-29 - 2020-12-31 - Office Closed - Office Closed"
        )

        self.assertEqual(rec.start_date, date.fromisoformat("2020-12-29"))
        self.assertEqual(rec.end_date, date.fromisoformat("2020-12-31"))
        self.assertEqual(rec.record_type.title, "Office Closed")
        self.assertEqual(rec.title, "Office Closed")
        self.assertEqual(rec.year, 2020)
