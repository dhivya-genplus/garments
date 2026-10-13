from datetime import datetime, date
from typing import Optional, Union
from django.utils import timezone
from core.exceptions import ValidationError


class FormatService:
    """
    FormatService: Ensures all date/time and numerical presentations strictly follow:
    - Display format: DMY ('DD/MM/YYYY') for dates and 'DD/MM/YYYY HH:MM' for datetimes.
    - Storage / Database format: standard ISO Date ('YYYY-MM-DD') in PostgreSQL/MySQL/SQLite.
    - Input parser: strictly accepts 'DD/MM/YYYY', 'DD-MM-YYYY', or 'YYYY-MM-DD'.
    """

    DATE_DISPLAY_FORMAT = "%d/%m/%Y"
    DATE_STORAGE_FORMAT = "%Y-%m-%d"
    DATETIME_DISPLAY_FORMAT = "%d/%m/%Y %H:%M"

    @classmethod
    def parse_date(cls, value: Union[str, date, None]) -> Optional[date]:
        """
        Parses date from input (DMY 'DD/MM/YYYY' or fallback YMD 'YYYY-MM-DD')
        into a Python datetime.date, which is stored as YMD in the database.
        """
        if value is None or value == "":
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value

        value_str = str(value).strip()
        for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(value_str, fmt).date()
            except ValueError:
                continue

        raise ValidationError(f"Invalid date '{value}'. Date must be in DMY ('DD/MM/YYYY') or YMD ('YYYY-MM-DD') format.")

    @classmethod
    def format_date(cls, value: Union[str, date, None]) -> str:
        """
        Formats a database date (YMD) strictly into DMY ('DD/MM/YYYY') for display / JSON output.
        """
        if not value:
            return ""
        if isinstance(value, str):
            value = cls.parse_date(value)
        return value.strftime(cls.DATE_DISPLAY_FORMAT)

    @classmethod
    def format_datetime(cls, dt: Optional[datetime]) -> str:
        """
        Formats datetime into 'DD/MM/YYYY HH:MM' in local timezone.
        """
        if not dt:
            return ""
        if timezone.is_aware(dt):
            dt = timezone.localtime(dt)
        return dt.strftime(cls.DATETIME_DISPLAY_FORMAT)

    @classmethod
    def to_storage_str(cls, value: Union[str, date, None]) -> Optional[str]:
        """
        Returns the ISO storage string 'YYYY-MM-DD' for SQL / ORM queries.
        """
        d = cls.parse_date(value)
        return d.strftime(cls.DATE_STORAGE_FORMAT) if d else None
