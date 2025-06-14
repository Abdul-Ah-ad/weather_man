import argparse
import csv
import os
import sys
from collections import defaultdict
from datetime import datetime
from enum import Enum

# Constants for weather data fields
DATE_FIELD = 'PKT'
RAW_DATE_FIELD = 'PKST'
DATE_FIELD_INDEX = 0
MAX_TEMP_INDEX = 1
MIN_TEMP_INDEX = 3
HUMIDITY_INDEX = 7

# Constants for stats dictionary keys
MAX_TEMP = 'max_temp'
MIN_TEMP = 'min_temp'
MAX_HUMIDITY = 'max_humidity'
MIN_HUMIDITY = 'min_humidity'

# Mapping of stats keys to their descriptive names
STATS_KEYS = {
    MAX_TEMP: 'max_temp',
    MIN_TEMP: 'min_temp',
    MAX_HUMIDITY: 'max_humidity',
    MIN_HUMIDITY: 'min_humidity'
}

# Default headers for fallback
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

def parse_weather_file(filepath):
    """
    Parses each row of a weather data file and yields valid tuples:
    (date, max_temp, min_temp, humidity).
    Skips invalid rows and continues with the next.
    """
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as file:
            reader = csv.reader(file)
            header = next(reader, [])
            if not header or header[DATE_FIELD_INDEX] == RAW_DATE_FIELD:
                header[DATE_FIELD_INDEX] = DATE_FIELD

            for row in reader:
                if not row or row[0].startswith('<!--'):
                    continue
                try:
                    date = datetime.strptime(row[DATE_FIELD_INDEX], '%Y-%m-%d')
                    max_temp = int(row[MAX_TEMP_INDEX]) if row[MAX_TEMP_INDEX] else None
                    min_temp = int(row[MIN_TEMP_INDEX]) if row[MIN_TEMP_INDEX] else None
                    humidity = int(row[HUMIDITY_INDEX]) if row[HUMIDITY_INDEX] else None
                    yield (date, max_temp, min_temp, humidity)#preventing data leakage
                except (ValueError, IndexError):
                    continue
    except (FileNotFoundError, IOError):
        pass

def generate_annual_stats(files):
    """
    Aggregates annual statistics: max/min temperature and humidity.
    Returns a dictionary: {year: {max_temp, min_temp, max_humidity, min_humidity}}
    """
    stats = defaultdict(lambda: {
        MAX_TEMP: float('-inf'),
        MIN_TEMP: float('inf'),
        MAX_HUMIDITY: float('-inf'),
        MIN_HUMIDITY: float('inf')
    })

    for file_path in files:
        for date, max_temp, min_temp, humidity in parse_weather_file(file_path):
            year = date.year
            if max_temp is not None:
                stats[year][MAX_TEMP] = max(stats[year][MAX_TEMP], max_temp)
            if min_temp is not None:
                stats[year][MIN_TEMP] = min(stats[year][MIN_TEMP], min_temp)
            if humidity is not None:
                stats[year][MAX_HUMIDITY] = max(stats[year][MAX_HUMIDITY], humidity)
                stats[year][MIN_HUMIDITY] = min(stats[year][MIN_HUMIDITY], humidity)

    return stats

def generate_annual_hottest_days(files):
    """
    Returns a dictionary: {year: {'temp': max_temp, 'date': 'YYYY-MM-DD'}}
    """
    hottest = {}
    for file_path in files:
        for date, max_temp, *_ in parse_weather_file(file_path):
            if max_temp is None:
                continue
            year = date.year
            if year not in hottest or max_temp > hottest[year]['temp']:
                hottest[year] = {'temp': max_temp, 'date': date.strftime('%Y-%m-%d')}
    return hottest

def print_annual_weather_stats(stats):
    """Prints the yearly max/min temperature and humidity statistics."""
    print('Year      Max Temp      Min Temp      Max Humidity      Min Humidity')
    print('--------------------------------------------------------------------')
    for year in sorted(stats.keys()):
        yearly_data = stats[year]
        max_temp = yearly_data[MAX_TEMP] if yearly_data[MAX_TEMP] != float('-inf') else '-'
        min_temp = yearly_data[MIN_TEMP] if yearly_data[MIN_TEMP] != float('inf') else '-'
        max_humidity = yearly_data[MAX_HUMIDITY] if yearly_data[MAX_HUMIDITY] != float('-inf') else '-'
        min_humidity = yearly_data[MIN_HUMIDITY] if yearly_data[MIN_HUMIDITY] != float('inf') else '-'
        print(f"{year:<10}{max_temp:^14}{min_temp:^14}{max_humidity:^18}{min_humidity:^14}")

def print_annual_hottest_days(hottest_days):
    """Prints the hottest day of each year with temperature and date."""
    print('Year      Date           Temp')
    print('------------------------------')
    for year in sorted(hottest_days.keys()):
        date = datetime.strptime(hottest_days[year]['date'], '%Y-%m-%d').strftime('%Y/%m/%d')
        print(f"{year:<10}{date:^15}{hottest_days[year]['temp']:>4}C")

def parse_cli_args():
    """Parses and returns command-line arguments."""
    parser = argparse.ArgumentParser(description='Weatherman - Weather Reports Generator')
    parser.add_argument(
        'report_number', type=int, choices=[report.value for report in ReportType],
        help='1 for Annual Weather Stats, 2 for Annual Hottest Day'
    )
    parser.add_argument(
        'data_directory', type=str,
        help='Path to directory containing weather .txt files'
    )
    return parser.parse_args()

def main():
    """Main function to handle report generation based on user input."""
    args = parse_cli_args()

    if not os.path.isdir(args.data_directory):
        print(f'Error: Directory not found: {args.data_directory}')
        sys.exit(1)

    files = collect_weather_data_files(args.data_directory)

    if args.report_number == ReportType.ANNUAL_STATS.value:
        stats = generate_annual_stats(files)
        print_annual_weather_stats(stats)
    elif args.report_number == ReportType.HOTTEST_DAY.value:
        hottest_days = generate_annual_hottest_days(files)
        print_annual_hottest_days(hottest_days)

if __name__ == '__main__':
    main()
