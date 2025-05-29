import os
import sys
import csv
from datetime import datetime
from collections import defaultdict

def get_weather_files(directory):
    """Return a list of .txt files in the specified directory."""
    files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.txt')]
    #print(f"Found {len(files)} .txt files in {directory}")
    return files

def parse_date(date_str):
    """Parse date string to datetime object, return None if invalid."""
    try:
        return datetime.strptime(date_str.strip(), '%Y-%m-%d')
    except ValueError:
        #print(f"Invalid date format: {date_str}")
        return None

def is_valid_temperature(temp):
    """Check if temperature is within plausible range (-10°C to 48°C)."""
    try:
        temp = int(temp)
        return -10 <= temp <= 48
    except ValueError:
        return False

def is_valid_humidity(humidity):
    """Check if humidity is within plausible range (0% to 100%)."""
    try:
        humidity = int(humidity)
        return 0 <= humidity <= 100
    except ValueError:
        return False

def parse_weather_data(files, report_type):
    """
    Parse weather data from files.
    For Report 1: Collect max/min temp and humidity per year.
    For Report 2: Collect hottest day per year.
    """
    if report_type == 1:
        yearly_stats = defaultdict(lambda: {
            'max_temp': float('-inf'), 'min_temp': float('inf'),
            'max_humidity': float('-inf'), 'min_humidity': float('inf')
        })
    else:
        yearly_hottest = defaultdict(lambda: {'temp': float('-inf'), 'date': ''})

    valid_rows = 0
    default_header = [
        'PKT', 'Max TemperatureC', 'Mean TemperatureC', 'Min TemperatureC',
        'Dew PointC', 'MeanDew PointC', 'Min DewpointC', 'Max Humidity',
        'Mean Humidity', 'Min Humidity'
    ]

    for filepath in files:
        #print(f"\nProcessing file: {filepath}")
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as file:
                raw_lines = file.readlines()
                lines = [line.strip() for line in raw_lines if line.strip() and not line.strip().startswith('<!--')]
                if not lines:
                    #print(f"  File is empty or only contains invalid lines")
                    continue

                reader = csv.reader(lines, delimiter=',', skipinitialspace=True)
                header = next(reader, None)
                if header and len(header) >= 10:
                    #print(f"  Header: {header[:10]}...")
                    if header[0] == 'PKST':
                        header[0] = 'PKT'
                else:
                    #print(f"  Invalid header: {header}")
                    header = default_header
                    reader = csv.reader(lines, delimiter=',', skipinitialspace=True)
                    #print(f"  Using default header: {header[:10]}...")

                row_count = 0
                for row in reader:
                    row_count += 1
                    if not row or all(cell.strip() == '' for cell in row):
                        #print(f"  Row {row_count}: Skipped (empty)")
                        continue
                    if len(row) < 10:
                        #print(f"  Row {row_count}: Skipped (too few columns): {row}")
                        continue

                    date = parse_date(row[0])
                    if not date:
                        #print(f"  Row {row_count}: Skipped (invalid date): {row[0]}")
                        continue

                    try:
                        max_temp = int(row[1]) if row[1].strip() and is_valid_temperature(row[1]) else None
                        min_temp = int(row[3]) if row[3].strip() and is_valid_temperature(row[3]) else None
                        max_humidity = int(row[7]) if row[7].strip() and is_valid_humidity(row[7]) else None
                        min_humidity = int(row[9]) if row[9].strip() and is_valid_humidity(row[9]) else None
                    except ValueError as e:
                        #print(f"  Row {row_count}: Skipped (invalid numeric data): {row[:5]}... - Error: {e}")
                        continue

                    if max_temp is None and min_temp is None and max_humidity is None and min_humidity is None:
                        #print(f"  Row {row_count}: Skipped (no valid data): {row[:5]}...")
                        continue

                    year = date.year
                    if report_type == 1:
                        if max_temp is not None:
                            yearly_stats[year]['max_temp'] = max(yearly_stats[year]['max_temp'], max_temp)
                        if min_temp is not None:
                            yearly_stats[year]['min_temp'] = min(yearly_stats[year]['min_temp'], min_temp)
                        if max_humidity is not None:
                            yearly_stats[year]['max_humidity'] = max(yearly_stats[year]['max_humidity'], max_humidity)
                        if min_humidity is not None:
                            yearly_stats[year]['min_humidity'] = min(yearly_stats[year]['min_humidity'], min_humidity)
                        valid_rows += 1
                        #print(f"  Row {row_count}: Processed (year {year})")
                    else:
                        if max_temp is not None and max_temp > yearly_hottest[year]['temp']:
                            yearly_hottest[year] = {'temp': max_temp, 'date': row[0]}
                            valid_rows += 1
                            #print(f"  Row {row_count}: Processed (year {year}, hottest temp {max_temp})")

        except Exception as e:
            #print(f"  Error processing {filepath}: {e}")
            continue

    #print(f"\nProcessed {valid_rows} valid rows")
    return yearly_stats if report_type == 1 else yearly_hottest

def print_report_1(yearly_stats):
    """Print Annual Weather Stats report."""
    if not yearly_stats:
        print("No valid data found.")
        return

    print("Year      Max Temp      Min Temp      Max Humidity      Min Humidity")
    print("--------------------------------------------------------------------")
    for year in sorted(yearly_stats.keys()):
        stats = yearly_stats[year]
        max_temp = stats['max_temp'] if stats['max_temp'] != float('-inf') else '-'
        min_temp = stats['min_temp'] if stats['min_temp'] != float('inf') else '-'
        max_humidity = stats['max_humidity'] if stats['max_humidity'] != float('-inf') else '-'
        min_humidity = stats['min_humidity'] if stats['min_humidity'] != float('inf') else '-'
        print(f"{year:<10}{max_temp:^14}{min_temp:^14}{max_humidity:^18}{min_humidity:^14}")

def print_report_2(yearly_hottest):
    """Print Annual Hottest Day report."""
    if not yearly_hottest:
        print("No valid data found.")
        return

    print("Year      Date           Temp")
    print("------------------------------")
    for year in sorted(yearly_hottest.keys()):
        data = yearly_hottest[year]
        if data['date']:
            date = datetime.strptime(data['date'], '%Y-%m-%d').strftime('%Y/%m/%d')
            print(f"{year:<10}{date:^15}{data['temp']:>4}C")

def main():
    """Main function to handle command-line arguments and generate reports."""
    if len(sys.argv) != 3:
        print("Usage: python weatherman.py [report_number] [data_directory]")
        print("report_number: 1 for Annual Weather Stats, 2 for Annual Hottest Day")
        sys.exit(1)

    try:
        report_number = int(sys.argv[1])
        if report_number not in [1, 2]:
            raise ValueError
    except ValueError:
        print("Invalid report number. Use 1 or 2.")
        sys.exit(1)

    data_directory = sys.argv[2]
    if not os.path.isdir(data_directory):
        print(f"Directory not found: {data_directory}")
        sys.exit(1)

    files = get_weather_files(data_directory)
    if not files:
        print("No data files found.")
        sys.exit(1)

    data = parse_weather_data(files, report_number)
    if report_number == 1:
        print_report_1(data)
    else:
        print_report_2(data)

if __name__ == "__main__":
    main()