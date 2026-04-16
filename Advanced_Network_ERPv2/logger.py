import csv
import os

def log_result(filename, row):
    os.makedirs("results", exist_ok=True)
    file_path = f"results/{filename}"

    file_exists = os.path.isfile(file_path)

    with open(file_path, 'a', newline='') as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow(["video", "ttff_ms", "method"])

        writer.writerow(row)