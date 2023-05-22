import logging
import pathlib
import re
from datetime import date

from django.utils import timezone

from teamsite_annual_leave.models.holiday_record import HolidayRecord
from teamsite_annual_leave.models.holiday_record_type import HolidayRecordType

logger = logging.getLogger(__name__)
_ptn = re.compile(
    r"(\d{4}-\d{2}-\d{2})\s*(-\s*(\d{4}-\d{2}-\d{2}))?\s*-\s(.+)\s*-\s(.+)"
)


def parse_bank_holiday_def(value: str) -> HolidayRecord:
    match = _ptn.match(value)
    if match is None:
        raise ValueError("Value does not match correct pattern")

    start = match.group(1)
    end = match.group(3)
    type_name = match.group(4)
    title = match.group(5)

    type_model = HolidayRecordType.objects.get(title=type_name.strip())

    if end is None:
        end = start

    start = date.fromisoformat(start)
    end = date.fromisoformat(end)

    record = HolidayRecord(
        start_date=start,
        end_date=end,
        record_type=type_model,
        title=title,
        year=start.year,
        created=timezone.now(),
    )

    return record


def read_holidays(stream):
    records = []
    for line in stream.readlines():
        if len(line.strip()) == 0 or line.startswith("#"):
            continue
        records.append(parse_bank_holiday_def(line))
    return records


def load_holiday_fixtures(fixtures_file=None):
    if fixtures_file is None:
        import teamsite_annual_leave

        fixtures_file = (
            pathlib.Path(teamsite_annual_leave.__file__).parent
            / "fixtures/uk-bank-holidays.yaml"
        )

    with open(fixtures_file, "rt") as FILE:
        return read_holidays(FILE)


def synchronise_holidays(holidays, testrun=False):
    current_records = HolidayRecord.objects.filter(
        record_type__title__in=["Public Holiday", "Office Closed"]
    )
    current_records_by_date = {r.start_date: r for r in current_records}

    for hol in holidays:
        current = current_records_by_date.get(hol.start_date)
        if current is not None:
            hol.pk = current.pk

        if hol.pk is None:
            logger.debug(f"Creating {hol}")
        else:
            logger.debug(f"Updating {hol}")

        if testrun:
            logger.warning("testrun -- skipping update")
        else:
            hol.save()
