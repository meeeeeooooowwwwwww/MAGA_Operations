#!/usr/bin/env python3
"""
Date Utility Module.

Provides functions for date and time operations.
Supports date formatting, parsing, and manipulation.
"""
import re
import datetime
import calendar
import time
import pytz
from typing import Dict, List, Optional, Union, Tuple, Any

def get_current_timestamp() -> int:
    """
    Get current Unix timestamp.
    
    Returns:
        int: Current timestamp in seconds
    """
    return int(time.time())

def get_current_timestamp_ms() -> int:
    """
    Get current Unix timestamp in milliseconds.
    
    Returns:
        int: Current timestamp in milliseconds
    """
    return int(time.time() * 1000)

def get_current_date() -> datetime.date:
    """
    Get current date.
    
    Returns:
        datetime.date: Current date
    """
    return datetime.date.today()

def get_current_datetime() -> datetime.datetime:
    """
    Get current datetime.
    
    Returns:
        datetime.datetime: Current datetime
    """
    return datetime.datetime.now()

def get_current_utc_datetime() -> datetime.datetime:
    """
    Get current UTC datetime.
    
    Returns:
        datetime.datetime: Current UTC datetime
    """
    return datetime.datetime.now(datetime.timezone.utc)

def timestamp_to_datetime(timestamp: Union[int, float], 
                         timezone: Optional[str] = None) -> datetime.datetime:
    """
    Convert Unix timestamp to datetime.
    
    Args:
        timestamp (int or float): Unix timestamp
        timezone (str, optional): Timezone name
        
    Returns:
        datetime.datetime: Converted datetime
    """
    dt = datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc)
    
    if timezone:
        dt = dt.astimezone(pytz.timezone(timezone))
    
    return dt

def datetime_to_timestamp(dt: datetime.datetime) -> int:
    """
    Convert datetime to Unix timestamp.
    
    Args:
        dt (datetime.datetime): Datetime object
        
    Returns:
        int: Unix timestamp
    """
    return int(dt.timestamp())

def format_datetime(dt: datetime.datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime as string.
    
    Args:
        dt (datetime.datetime): Datetime object
        format_str (str, optional): Format string
        
    Returns:
        str: Formatted datetime
    """
    return dt.strftime(format_str)

def parse_datetime(datetime_str: str, format_str: str = "%Y-%m-%d %H:%M:%S",
                 timezone: Optional[str] = None) -> datetime.datetime:
    """
    Parse datetime from string.
    
    Args:
        datetime_str (str): Datetime string
        format_str (str, optional): Format string
        timezone (str, optional): Timezone name
        
    Returns:
        datetime.datetime: Parsed datetime
    """
    dt = datetime.datetime.strptime(datetime_str, format_str)
    
    if timezone:
        tz = pytz.timezone(timezone)
        dt = tz.localize(dt)
    
    return dt

def parse_date(date_str: str, format_str: str = "%Y-%m-%d") -> datetime.date:
    """
    Parse date from string.
    
    Args:
        date_str (str): Date string
        format_str (str, optional): Format string
        
    Returns:
        datetime.date: Parsed date
    """
    return datetime.datetime.strptime(date_str, format_str).date()

def parse_iso_datetime(iso_str: str) -> datetime.datetime:
    """
    Parse ISO 8601 datetime string.
    
    Args:
        iso_str (str): ISO datetime string
        
    Returns:
        datetime.datetime: Parsed datetime
    """
    return datetime.datetime.fromisoformat(iso_str.replace('Z', '+00:00'))

def to_iso_format(dt: Union[datetime.datetime, datetime.date]) -> str:
    """
    Convert datetime to ISO 8601 format.
    
    Args:
        dt (datetime.datetime or datetime.date): Datetime or date object
        
    Returns:
        str: ISO 8601 formatted string
    """
    if isinstance(dt, datetime.date) and not isinstance(dt, datetime.datetime):
        return dt.isoformat()
    
    return dt.isoformat()

def add_days(dt: Union[datetime.datetime, datetime.date], days: int) -> Union[datetime.datetime, datetime.date]:
    """
    Add days to date or datetime.
    
    Args:
        dt (datetime.datetime or datetime.date): Date or datetime object
        days (int): Number of days to add
        
    Returns:
        datetime.datetime or datetime.date: New date or datetime
    """
    return dt + datetime.timedelta(days=days)

def add_hours(dt: datetime.datetime, hours: int) -> datetime.datetime:
    """
    Add hours to datetime.
    
    Args:
        dt (datetime.datetime): Datetime object
        hours (int): Number of hours to add
        
    Returns:
        datetime.datetime: New datetime
    """
    return dt + datetime.timedelta(hours=hours)

def add_minutes(dt: datetime.datetime, minutes: int) -> datetime.datetime:
    """
    Add minutes to datetime.
    
    Args:
        dt (datetime.datetime): Datetime object
        minutes (int): Number of minutes to add
        
    Returns:
        datetime.datetime: New datetime
    """
    return dt + datetime.timedelta(minutes=minutes)

def add_seconds(dt: datetime.datetime, seconds: int) -> datetime.datetime:
    """
    Add seconds to datetime.
    
    Args:
        dt (datetime.datetime): Datetime object
        seconds (int): Number of seconds to add
        
    Returns:
        datetime.datetime: New datetime
    """
    return dt + datetime.timedelta(seconds=seconds)

def date_diff_in_days(date1: Union[datetime.datetime, datetime.date], 
                     date2: Union[datetime.datetime, datetime.date]) -> int:
    """
    Calculate days between two dates.
    
    Args:
        date1 (datetime.datetime or datetime.date): First date
        date2 (datetime.datetime or datetime.date): Second date
        
    Returns:
        int: Days between dates
    """
    # Extract date components if datetime objects
    if isinstance(date1, datetime.datetime):
        date1 = date1.date()
    if isinstance(date2, datetime.datetime):
        date2 = date2.date()
    
    return (date2 - date1).days

def time_diff_in_seconds(dt1: datetime.datetime, dt2: datetime.datetime) -> float:
    """
    Calculate seconds between two datetimes.
    
    Args:
        dt1 (datetime.datetime): First datetime
        dt2 (datetime.datetime): Second datetime
        
    Returns:
        float: Seconds between datetimes
    """
    return (dt2 - dt1).total_seconds()

def date_range(start_date: Union[datetime.datetime, datetime.date], 
              end_date: Union[datetime.datetime, datetime.date], 
              include_end: bool = True) -> List[datetime.date]:
    """
    Generate range of dates.
    
    Args:
        start_date (datetime.datetime or datetime.date): Start date
        end_date (datetime.datetime or datetime.date): End date
        include_end (bool, optional): Include end date
        
    Returns:
        list: List of dates
    """
    # Extract date components if datetime objects
    if isinstance(start_date, datetime.datetime):
        start_date = start_date.date()
    if isinstance(end_date, datetime.datetime):
        end_date = end_date.date()
    
    # Adjust end date if not including it
    if not include_end:
        end_date = end_date - datetime.timedelta(days=1)
    
    # Generate date range
    result = []
    current_date = start_date
    
    while current_date <= end_date:
        result.append(current_date)
        current_date += datetime.timedelta(days=1)
    
    return result

def get_month_name(month: int) -> str:
    """
    Get month name from month number.
    
    Args:
        month (int): Month number (1-12)
        
    Returns:
        str: Month name
    """
    if month < 1 or month > 12:
        raise ValueError("Month must be between 1 and 12")
    
    return calendar.month_name[month]

def get_month_abbr(month: int) -> str:
    """
    Get month abbreviation from month number.
    
    Args:
        month (int): Month number (1-12)
        
    Returns:
        str: Month abbreviation
    """
    if month < 1 or month > 12:
        raise ValueError("Month must be between 1 and 12")
    
    return calendar.month_abbr[month]

def get_day_name(weekday: int) -> str:
    """
    Get day name from weekday number.
    
    Args:
        weekday (int): Weekday number (0-6, Monday is 0)
        
    Returns:
        str: Day name
    """
    if weekday < 0 or weekday > 6:
        raise ValueError("Weekday must be between 0 and 6")
    
    return calendar.day_name[weekday]

def get_day_abbr(weekday: int) -> str:
    """
    Get day abbreviation from weekday number.
    
    Args:
        weekday (int): Weekday number (0-6, Monday is 0)
        
    Returns:
        str: Day abbreviation
    """
    if weekday < 0 or weekday > 6:
        raise ValueError("Weekday must be between 0 and 6")
    
    return calendar.day_abbr[weekday]

def get_first_day_of_month(year: int, month: int) -> datetime.date:
    """
    Get first day of month.
    
    Args:
        year (int): Year
        month (int): Month
        
    Returns:
        datetime.date: First day of month
    """
    return datetime.date(year, month, 1)

def get_last_day_of_month(year: int, month: int) -> datetime.date:
    """
    Get last day of month.
    
    Args:
        year (int): Year
        month (int): Month
        
    Returns:
        datetime.date: Last day of month
    """
    # Get days in month
    _, days_in_month = calendar.monthrange(year, month)
    
    return datetime.date(year, month, days_in_month)

def get_days_in_month(year: int, month: int) -> int:
    """
    Get number of days in month.
    
    Args:
        year (int): Year
        month (int): Month
        
    Returns:
        int: Days in month
    """
    _, days_in_month = calendar.monthrange(year, month)
    return days_in_month

def get_first_day_of_year(year: int) -> datetime.date:
    """
    Get first day of year.
    
    Args:
        year (int): Year
        
    Returns:
        datetime.date: First day of year
    """
    return datetime.date(year, 1, 1)

def get_last_day_of_year(year: int) -> datetime.date:
    """
    Get last day of year.
    
    Args:
        year (int): Year
        
    Returns:
        datetime.date: Last day of year
    """
    return datetime.date(year, 12, 31)

def is_leap_year(year: int) -> bool:
    """
    Check if year is leap year.
    
    Args:
        year (int): Year
        
    Returns:
        bool: True if leap year
    """
    return calendar.isleap(year)

def get_quarter(date: Union[datetime.datetime, datetime.date]) -> int:
    """
    Get quarter from date.
    
    Args:
        date (datetime.datetime or datetime.date): Date
        
    Returns:
        int: Quarter (1-4)
    """
    month = date.month
    return (month - 1) // 3 + 1

def get_quarter_range(year: int, quarter: int) -> Tuple[datetime.date, datetime.date]:
    """
    Get start and end dates of quarter.
    
    Args:
        year (int): Year
        quarter (int): Quarter (1-4)
        
    Returns:
        tuple: (start_date, end_date)
    """
    if quarter < 1 or quarter > 4:
        raise ValueError("Quarter must be between 1 and 4")
    
    start_month = (quarter - 1) * 3 + 1
    end_month = quarter * 3
    
    start_date = datetime.date(year, start_month, 1)
    end_date = get_last_day_of_month(year, end_month)
    
    return (start_date, end_date)

def get_fiscal_year_quarter(date: Union[datetime.datetime, datetime.date], 
                           fiscal_start_month: int = 10) -> Tuple[int, int]:
    """
    Get fiscal year and quarter from date.
    
    Args:
        date (datetime.datetime or datetime.date): Date
        fiscal_start_month (int, optional): Fiscal year start month (1-12)
        
    Returns:
        tuple: (fiscal_year, fiscal_quarter)
    """
    if fiscal_start_month < 1 or fiscal_start_month > 12:
        raise ValueError("Fiscal start month must be between 1 and 12")
    
    month = date.month
    year = date.year
    
    # Adjust for fiscal year
    if month < fiscal_start_month:
        fiscal_year = year - 1
    else:
        fiscal_year = year
    
    # Calculate fiscal quarter
    fiscal_month = (month - fiscal_start_month) % 12 + 1
    fiscal_quarter = (fiscal_month - 1) // 3 + 1
    
    return (fiscal_year, fiscal_quarter)

def date_to_week_tuple(date: Union[datetime.datetime, datetime.date]) -> Tuple[int, int]:
    """
    Get ISO year and week number from date.
    
    Args:
        date (datetime.datetime or datetime.date): Date
        
    Returns:
        tuple: (iso_year, iso_week)
    """
    # Extract date component if datetime
    if isinstance(date, datetime.datetime):
        date = date.date()
    
    return date.isocalendar()[0:2]

def week_tuple_to_date(year_week_tuple: Tuple[int, int], 
                      weekday: int = 1) -> datetime.date:
    """
    Get date from ISO year and week number.
    
    Args:
        year_week_tuple (tuple): (iso_year, iso_week)
        weekday (int, optional): Weekday (1-7, Monday is 1)
        
    Returns:
        datetime.date: Date
    """
    year, week = year_week_tuple
    
    # Create date from ISO year, week, and day
    return datetime.date.fromisocalendar(year, week, weekday)

def get_next_weekday(date: Union[datetime.datetime, datetime.date], 
                    weekday: int) -> datetime.date:
    """
    Get next specified weekday from date.
    
    Args:
        date (datetime.datetime or datetime.date): Date
        weekday (int): Weekday (0-6, Monday is 0)
        
    Returns:
        datetime.date: Next weekday
    """
    # Extract date component if datetime
    if isinstance(date, datetime.datetime):
        date = date.date()
    
    days_ahead = weekday - date.weekday()
    
    # Handle if weekday has already occurred this week
    if days_ahead <= 0:
        days_ahead += 7
    
    return date + datetime.timedelta(days=days_ahead)

def get_previous_weekday(date: Union[datetime.datetime, datetime.date], 
                        weekday: int) -> datetime.date:
    """
    Get previous specified weekday from date.
    
    Args:
        date (datetime.datetime or datetime.date): Date
        weekday (int): Weekday (0-6, Monday is 0)
        
    Returns:
        datetime.date: Previous weekday
    """
    # Extract date component if datetime
    if isinstance(date, datetime.datetime):
        date = date.date()
    
    days_behind = date.weekday() - weekday
    
    # Handle if weekday hasn't occurred this week
    if days_behind < 0:
        days_behind += 7
    
    return date - datetime.timedelta(days=days_behind)

def parse_fuzzy_date(date_str: str) -> Optional[datetime.date]:
    """
    Parse date from fuzzy string.
    
    Args:
        date_str (str): Date string
        
    Returns:
        datetime.date or None: Parsed date
    """
    # Common date formats
    formats = [
        "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%B %d, %Y", "%b %d, %Y",
        "%Y/%m/%d", "%d-%m-%Y", "%d %B %Y", "%d %b %Y"
    ]
    
    # Try each format
    for format_str in formats:
        try:
            return datetime.datetime.strptime(date_str, format_str).date()
        except ValueError:
            continue
    
    # Special cases
    today = datetime.date.today()
    
    # Today, yesterday, tomorrow
    lower_str = date_str.lower()
    if lower_str == "today":
        return today
    elif lower_str == "yesterday":
        return today - datetime.timedelta(days=1)
    elif lower_str == "tomorrow":
        return today + datetime.timedelta(days=1)
    
    # N days ago/from now
    match = re.match(r"(\d+) days? ago", lower_str)
    if match:
        return today - datetime.timedelta(days=int(match.group(1)))
    
    match = re.match(r"(\d+) days? from now", lower_str)
    if match:
        return today + datetime.timedelta(days=int(match.group(1)))
    
    # Last/next day of week
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    for i, day in enumerate(days):
        if lower_str == f"last {day}":
            return get_previous_weekday(today, i)
        elif lower_str == f"next {day}":
            return get_next_weekday(today, i)
    
    # Failed to parse
    return None

def get_timezone_list() -> List[str]:
    """
    Get list of available timezones.
    
    Returns:
        list: List of timezone names
    """
    return pytz.all_timezones

def convert_timezone(dt: datetime.datetime, target_timezone: str) -> datetime.datetime:
    """
    Convert datetime to different timezone.
    
    Args:
        dt (datetime.datetime): Datetime object
        target_timezone (str): Target timezone name
        
    Returns:
        datetime.datetime: Converted datetime
    """
    # Ensure datetime is aware
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    
    # Convert to target timezone
    target_tz = pytz.timezone(target_timezone)
    return dt.astimezone(target_tz)

def is_business_day(date: Union[datetime.datetime, datetime.date], 
                   holidays: List[datetime.date] = None) -> bool:
    """
    Check if date is business day.
    
    Args:
        date (datetime.datetime or datetime.date): Date to check
        holidays (list, optional): List of holiday dates
        
    Returns:
        bool: True if business day
    """
    # Extract date component if datetime
    if isinstance(date, datetime.datetime):
        date = date.date()
    
    # Check if weekend
    if date.weekday() >= 5:  # Saturday or Sunday
        return False
    
    # Check if holiday
    if holidays and date in holidays:
        return False
    
    return True

def add_business_days(date: Union[datetime.datetime, datetime.date], 
                     days: int, 
                     holidays: List[datetime.date] = None) -> datetime.date:
    """
    Add business days to date.
    
    Args:
        date (datetime.datetime or datetime.date): Start date
        days (int): Number of business days to add
        holidays (list, optional): List of holiday dates
        
    Returns:
        datetime.date: Result date
    """
    # Extract date component if datetime
    if isinstance(date, datetime.datetime):
        date = date.date()
    
    # Initialize result
    result = date
    days_remaining = days
    
    # Positive or negative days
    step = 1 if days >= 0 else -1
    
    while days_remaining != 0:
        result += datetime.timedelta(days=step)
        if is_business_day(result, holidays):
            days_remaining -= step
    
    return result

def get_age(birth_date: Union[datetime.datetime, datetime.date], 
           relative_to: Union[datetime.datetime, datetime.date] = None) -> int:
    """
    Calculate age from birth date.
    
    Args:
        birth_date (datetime.datetime or datetime.date): Birth date
        relative_to (datetime.datetime or datetime.date, optional): Reference date
        
    Returns:
        int: Age in years
    """
    # Extract date components if datetime objects
    if isinstance(birth_date, datetime.datetime):
        birth_date = birth_date.date()
    
    if relative_to is None:
        relative_to = datetime.date.today()
    elif isinstance(relative_to, datetime.datetime):
        relative_to = relative_to.date()
    
    # Calculate age
    age = relative_to.year - birth_date.year
    
    # Adjust if birthday hasn't occurred yet this year
    if (relative_to.month, relative_to.day) < (birth_date.month, birth_date.day):
        age -= 1
    
    return age

def format_relative_time(dt: datetime.datetime, 
                        now: Optional[datetime.datetime] = None,
                        include_seconds: bool = False) -> str:
    """
    Format datetime as relative time.
    
    Args:
        dt (datetime.datetime): Datetime to format
        now (datetime.datetime, optional): Reference datetime
        include_seconds (bool, optional): Include seconds
        
    Returns:
        str: Relative time string
    """
    if now is None:
        now = datetime.datetime.now(datetime.timezone.utc)
    
    # Ensure both datetimes are aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=datetime.timezone.utc)
    
    # Calculate time difference
    diff = now - dt
    seconds = diff.total_seconds()
    
    # Future time
    if seconds < 0:
        seconds = abs(seconds)
        if seconds < 60:
            return "in a few seconds" if not include_seconds else f"in {int(seconds)} seconds"
        elif seconds < 3600:
            return f"in {int(seconds // 60)} minutes"
        elif seconds < 86400:
            return f"in {int(seconds // 3600)} hours"
        elif seconds < 604800:
            return f"in {int(seconds // 86400)} days"
        elif seconds < 2592000:
            return f"in {int(seconds // 604800)} weeks"
        elif seconds < 31536000:
            return f"in {int(seconds // 2592000)} months"
        else:
            return f"in {int(seconds // 31536000)} years"
    
    # Past time
    if seconds < 60:
        return "just now" if not include_seconds else f"{int(seconds)} seconds ago"
    elif seconds < 3600:
        return f"{int(seconds // 60)} minutes ago"
    elif seconds < 86400:
        return f"{int(seconds // 3600)} hours ago"
    elif seconds < 604800:
        return f"{int(seconds // 86400)} days ago"
    elif seconds < 2592000:
        return f"{int(seconds // 604800)} weeks ago"
    elif seconds < 31536000:
        return f"{int(seconds // 2592000)} months ago"
    else:
        return f"{int(seconds // 31536000)} years ago"

if __name__ == "__main__":
    # Test date utilities
    print(f"Current timestamp: {get_current_timestamp()}")
    print(f"Current date: {get_current_date()}")
    print(f"Current datetime: {get_current_datetime()}")
    print(f"Current UTC datetime: {get_current_utc_datetime()}")
    
    # Test date formatting
    now = get_current_datetime()
    print(f"Formatted datetime: {format_datetime(now)}")
    print(f"ISO format: {to_iso_format(now)}")
    
    # Test date manipulation
    print(f"Tomorrow: {add_days(get_current_date(), 1)}")
    print(f"Next hour: {add_hours(now, 1)}")
    
    # Test date ranges
    start = get_current_date()
    end = add_days(start, 7)
    print(f"Date range: {date_range(start, end)}")
    
    # Test quarter functions
    print(f"Current quarter: {get_quarter(now)}")
    
    # Test relative time
    past = add_days(now, -1)
    future = add_days(now, 1)
    print(f"Relative time (past): {format_relative_time(past)}")
    print(f"Relative time (future): {format_relative_time(future)}")
    
    # Test business days
    print(f"Is business day: {is_business_day(now)}")
    print(f"Add 5 business days: {add_business_days(now, 5)}")
    
    # Test fuzzy date parsing
    print(f"Parse 'yesterday': {parse_fuzzy_date('yesterday')}")
    print(f"Parse 'next monday': {parse_fuzzy_date('next monday')}")
    print(f"Parse '5 days ago': {parse_fuzzy_date('5 days ago')}") 