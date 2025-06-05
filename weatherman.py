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
MAX_TEMP_INDEX = 1
MIN_TEMP_INDEX = 3
HUMIDITY_INDEX = 7

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
    return (
        os.path.join(directory, filename)
        for filename in os.listdir(directory)
        if filename.endswith('.txt')
    )

def parse_weather_file(filepath):
    """
    Generator that parses each row of a weather data file into a tuple containing:
    (date, max_temp, min_temp, humidity). Skips invalid rows.
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
                    max_temp = int(row[MAX_TEMP_INDEX]) if row[MAX_TEMP_INDEX] != '' else None
                    min_temp = int(row[MIN_TEMP_INDEX]) if row[MIN_TEMP_INDEX] != '' else None
                    humidity = int(row[HUMIDITY_INDEX]) if row[HUMIDITY_INDEX] != '' else None
                    yield date, max_temp, min_temp, humidity
                except (ValueError, IndexError):
                    continue
    except (FileNotFoundError, IOError):
        return

def generate_annual_stats(files):
    """
    Generator that yields aggregated annual statistics:
    max/min temperature and humidity per year.
    """
    stats = defaultdict(lambda: {
        'max_temp': float('-inf'),
        'min_temp': float('inf'),
        'max_humidity': float('-inf'),
        'min_humidity': float('inf')
    })

    for file in files:
        for date, max_temp, min_temp, humidity in parse_weather_file(file):
            year = date.year
            if max_temp is not None:
                stats[year]['max_temp'] = max(stats[year]['max_temp'], max_temp)
            if min_temp is not None:
                stats[year]['min_temp'] = min(stats[year]['min_temp'], min_temp)
            if humidity is not None:
                stats[year]['max_humidity'] = max(stats[year]['max_humidity'], humidity)
                stats[year]['min_humidity'] = min(stats[year]['min_humidity'], humidity)

    for year, data in stats.items():
        yield year, data

def generate_annual_hottest_days(files):
    """
    Generator that yields the hottest day (max temperature and date) per year.
    """
    hottest = {}
    for file in files:
        for date, max_temp, *_ in parse_weather_file(file):
            if max_temp is None:
                continue
            year = date.year
            if year not in hottest or max_temp > hottest[year]['temp']:
                hottest[year] = {'temp': max_temp, 'date': date.strftime('%Y-%m-%d')}
    for year, data in hottest.items():
        yield year, data

def print_annual_weather_stats(stats):
    """Prints the yearly max/min temperature and humidity statistics."""
    print('Year      Max Temp      Min Temp      Max Humidity      Min Humidity')
    print('--------------------------------------------------------------------')
    for year, s in sorted(stats):
        max_temp = s['max_temp'] if s['max_temp'] != float('-inf') else '-'
        min_temp = s['min_temp'] if s['min_temp'] != float('inf') else '-'
        max_humidity = s['max_humidity'] if s['max_humidity'] != float('-inf') else '-'
        min_humidity = s['min_humidity'] if s['min_humidity'] != float('inf') else '-'
        print(f"{year:<10}{max_temp:^14}{min_temp:^14}{max_humidity:^18}{min_humidity:^14}")

def print_annual_hottest_days(hottest_days):
    """Prints the hottest day of each year with temperature and date."""
    print('Year      Date           Temp')
    print('------------------------------')
    for year, data in sorted(hottest_days):
        date = datetime.strptime(data['date'], '%Y-%m-%d').strftime('%Y/%m/%d')
        print(f"{year:<10}{date:^15}{data['temp']:>4}C")

def main():
    """Main function to handle CLI arguments and generate requested report."""
    parser = argparse.ArgumentParser(description='Weatherman - Weather Reports Generator')
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

    if args.report_number == 1:
        stats = generate_annual_stats(files)
        print_annual_weather_stats(stats)
    else:
        hottest_days = generate_annual_hottest_days(files)
        print_annual_hottest_days(hottest_days)

if __name__ == '__main__':
    main()
