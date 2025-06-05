import argparse
import csv
import os
import sys
from collections import defaultdict
from datetime import datetime
from enum import Enum

# Declaring all constants
DATE_FIELD = 'PKT'
RAW_DATE_FIELD = 'PKST'
DATE_FIELD_INDEX = 0
MAX_TEMP_FIELD = 'Max TemperatureC'
MIN_TEMP_FIELD = 'Min TemperatureC'
MAX_HUMIDITY_FIELD = 'Max Humidity'
MIN_HUMIDITY_FIELD = 'Min Humidity'

DEFAULT_HEADER = [
    'PKT', 'Max TemperatureC', 'Mean TemperatureC', 'Min TemperatureC',
    'Dew PointC', 'MeanDew PointC', 'Min DewpointC', 'Max Humidity',
    'Mean Humidity', 'Min Humidity'
]


class ReportType(Enum):
    """Defines the types of reports supported."""
    ANNUAL_STATS = 1
    HOTTEST_DAY = 2


def collect_weather_data_files(directory):
    """Returns a list of all .txt weather data files in the given directory."""
    return [
        os.path.join(directory, filename)
        for filename in os.listdir(directory)
        if filename.endswith('.txt')
    ]


def parse_date(date_str):
    """Parses a date string into a datetime object. Returns None if invalid."""
    try:
        return datetime.strptime(date_str.strip(), '%Y-%m-%d')
    except ValueError:
        return None


def is_valid_temperature(temp):
    """Checks if the given temperature is a valid integer within -10 to 48 C."""
    try:
        temp = int(temp)
        return -10 <= temp <= 48
    except (ValueError, TypeError):
        return False


def is_valid_humidity(humidity):
    """Checks if the given humidity is a valid integer between 0 and 100%."""
    try:
        humidity = int(humidity)
        return 0 <= humidity <= 100
    except (ValueError, TypeError):
        return False


def fix_header_fieldnames(fieldnames):
    """Replaces 'PKST' with 'PKT' in the header fields if needed."""
    if not fieldnames:
        return DEFAULT_HEADER
    fieldnames[DATE_FIELD_INDEX] = (
        DATE_FIELD
        if fieldnames[DATE_FIELD_INDEX] == RAW_DATE_FIELD
        else fieldnames[DATE_FIELD_INDEX]
    )
    return fieldnames


def parse_weather_file(filepath):
    """Parses a weather data file and returns a list of record dictionaries."""
    weather_records = []
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as file:
            lines = [
                line.strip()
                for line in file.readlines()
                if line.strip() and not line.strip().startswith('<!--')
            ]
            if not lines:
                return []

            reader = csv.DictReader(lines)
            reader.fieldnames = fix_header_fieldnames(reader.fieldnames)

            for row in reader:
                date = parse_date(row.get(DATE_FIELD))
                if not date:
                    continue

                try:
                    max_temp = (
                        int(row[MAX_TEMP_FIELD])
                        if is_valid_temperature(row[MAX_TEMP_FIELD])
                        else None
                    )
                    min_temp = (
                        int(row[MIN_TEMP_FIELD])
                        if is_valid_temperature(row[MIN_TEMP_FIELD])
                        else None
                    )
                    max_humidity = (
                        int(row[MAX_HUMIDITY_FIELD])
                        if is_valid_humidity(row[MAX_HUMIDITY_FIELD])
                        else None
                    )
                    min_humidity = (
                        int(row[MIN_HUMIDITY_FIELD])
                        if is_valid_humidity(row[MIN_HUMIDITY_FIELD])
                        else None
                    )
                except (ValueError, KeyError):
                    continue

                weather_records.append({
                    'date': date,
                    'max_temp': max_temp,
                    'min_temp': min_temp,
                    'max_humidity': max_humidity,
                    'min_humidity': min_humidity
                })

    except FileNotFoundError:
        print(f"File not found: {filepath}")
    except IOError:
        print(f"Error reading file: {filepath}")

    return weather_records


def aggregate_annual_stats(records):
    """Aggregates yearly statistics like max/min temperature and humidity."""
    stats = defaultdict(lambda: {
        'max_temp': float('-inf'),
        'min_temp': float('inf'),
        'max_humidity': float('-inf'),
        'min_humidity': float('inf')
    })

    for record in records:
        year = record['date'].year
        if record['max_temp'] is not None:
            stats[year]['max_temp'] = max(
                stats[year]['max_temp'], record['max_temp']
            )
        if record['min_temp'] is not None:
            stats[year]['min_temp'] = min(
                stats[year]['min_temp'], record['min_temp']
            )
        if record['max_humidity'] is not None:
            stats[year]['max_humidity'] = max(
                stats[year]['max_humidity'], record['max_humidity']
            )
        if record['min_humidity'] is not None:
            stats[year]['min_humidity'] = min(
                stats[year]['min_humidity'], record['min_humidity']
            )

    return stats


def get_annual_hottest_days(records):
    """Returns the hottest day of each year based on max temperature."""
    hottest_days = defaultdict(
        lambda: {'temp': float('-inf'), 'date': None}
    )

    for record in records:
        year = record['date'].year
        temp = record['max_temp']
        if temp is not None and temp > hottest_days[year]['temp']:
            hottest_days[year] = {
                'temp': temp,
                'date': record['date'].strftime('%Y-%m-%d')
            }

    return hottest_days


def parse_weather_data(files, report_type: ReportType):
    """Parses data from files and returns statistics or hottest day info."""
    all_records = []
    for file in files:
        all_records.extend(parse_weather_file(file))

    if report_type == ReportType.ANNUAL_STATS:
        return aggregate_annual_stats(all_records)
    else:
        return get_annual_hottest_days(all_records)


def print_annual_weather_stats(stats):
    """Prints the yearly max/min temperature and humidity statistics."""
    if not stats:
        print('No valid data found.')
        return

    print('Year      Max Temp      Min Temp      Max Humidity      '
          'Min Humidity')
    print('--------------------------------------------------------------------')
    for year in sorted(stats.keys()):
        s = stats[year]
        max_temp = s['max_temp'] if s['max_temp'] != float('-inf') else '-'
        min_temp = s['min_temp'] if s['min_temp'] != float('inf') else '-'
        max_humidity = (
            s['max_humidity'] if s['max_humidity'] != float('-inf') else '-'
        )
        min_humidity = (
            s['min_humidity'] if s['min_humidity'] != float('inf') else '-'
        )
        print(f"{year:<10}{max_temp:^14}{min_temp:^14}"
              f"{max_humidity:^18}{min_humidity:^14}")


def print_annual_hottest_days(hottest_days):
    """Prints the hottest day of each year with temperature and date."""
    if not hottest_days:
        print("No valid data found.")
        return

    print('Year      Date           Temp')
    print('------------------------------')
    for year in sorted(hottest_days.keys()):
        data = hottest_days[year]
        if data['date']:
            date = datetime.strptime(
                data['date'], '%Y-%m-%d'
            ).strftime('%Y/%m/%d')
            print(f"{year:<10}{date:^15}{data['temp']:>4}C")


def main():
    """Main function to handle CLI arguments and generate requested report."""
    parser = argparse.ArgumentParser(
        description='Weatherman - Weather Reports Generator'
    )
    parser.add_argument(
        'report_number', type=int, choices=[1, 2],
        help='1 for Annual Weather Stats, 2 for Annual Hottest Day'
    )
    parser.add_argument(
        'data_directory', type=str,
        help='Path to directory containing weather .txt files'
    )

    args = parser.parse_args()

    if not os.path.isdir(args.data_directory):
        print(f'Directory not found: {args.data_directory}')
        sys.exit(1)

    files = collect_weather_data_files(args.data_directory)
    if not files:
        print('No data files found.')
        sys.exit(1)

    report_type = ReportType(args.report_number)
    data = parse_weather_data(files, report_type)

    if report_type == ReportType.ANNUAL_STATS:
        print_annual_weather_stats(data)
    else:
        print_annual_hottest_days(data)


if __name__ == '__main__':
    main()
