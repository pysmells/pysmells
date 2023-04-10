import os
import re
import argparse
import subprocess
import csv
from collections import Counter, defaultdict
from tabulate import tabulate


def analyze_file(directory, file_path):
    print(f"Analyzing the file: {file_path}\n")

    # Run Pylint
    process = subprocess.run(["pylint", file_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             universal_newlines=True, check=False)
    pylint_output = process.stdout

    alert_count = Counter()
    alert_details = defaultdict(list)

    alert_pattern = re.compile(r'([CRWEF]\d{4})')

    alert_type_names = {
        'C': 'Convention',
        'R': 'Refactor',
        'W': 'Warning',
        'E': 'Error',
        'F': 'Fatal'
    }

    for line in pylint_output.split("\n"):
        match = alert_pattern.search(line)
        if match:
            alert_code = match.group(0)
            alert_type = alert_code[0]
            alert_count[alert_type] += 1
            alert_details[alert_type].append(alert_code)

    return alert_count, alert_details

def export_to_csv(table_data, headers, csv_output):
    with open(csv_output, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(headers)
        for row in table_data:
            csv_writer.writerow(row)

def main():
    parser = argparse.ArgumentParser(description="Analyze Python files in the specified directories.")
    parser.add_argument("-p", "--project", required=True, help="The project directory containing the subdirectories with Python files to analyze.")
    parser.add_argument("-s", "--subdirs", nargs='+', required=True, help="The list of subdirectories in the project directory, each representing a software.")
    parser.add_argument("-csv", "--csv_output", help="The path and file name for the CSV output.", type=str)

    args = parser.parse_args()
    project_directory = os.path.abspath(args.project)
    subdirectories = args.subdirs
    csv_output = args.csv_output

    print(f"Project directory (absolute path): {project_directory}")

    table_data = []

    for subdir in subdirectories:
        current_directory = os.path.abspath(os.path.join(project_directory, subdir))
        print(f"Analyzing subdirectory (absolute path): {current_directory}")

        subdir_alert_count = Counter()
        subdir_alert_details = defaultdict(list)

        if os.path.isdir(current_directory):
            for root, dirs, files in os.walk(current_directory):
                for file_name in files:
                    if file_name.endswith(".py"):
                        file_path = os.path.join(root, file_name)
                        file_alert_count, file_alert_details = analyze_file(root, file_path)

                        subdir_alert_count.update(file_alert_count)
                        for alert_type, alert_codes in file_alert_details.items():
                            subdir_alert_details[alert_type].extend(alert_codes)

                        file_row = [file_path, sum(file_alert_count.values())]
                        for alert_type in 'CRWEF':
                            file_row.append(file_alert_count[alert_type])

                        file_row.append(", ".join(sorted(set(alert_code for alert_codes in file_alert_details.values() for alert_code in alert_codes))))
                        table_data.append(file_row)

            subdir_row = [current_directory, sum(subdir_alert_count.values())]
            for alert_type in 'CRWEF':
                subdir_row.append(subdir_alert_count[alert_type])

            subdir_row.append(", ".join(sorted(set(alert_code for alert_codes in subdir_alert_details.values() for alert_code in alert_codes))))
            table_data.append(subdir_row)
        else:
            print(f"Subdirectory not found: {current_directory}")

    headers = ["Path", "Total Alerts", "Convention", "Refactor", "Warning", "Error", "Fatal", "Alert Codes"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

    if csv_output:
        export_to_csv(table_data, headers, csv_output)
        print(f"CSV file exported to: {csv_output}")

if __name__ == "__main__":
    main()

