import csv
import datetime
import os
import re
import time
import serial

SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE = 115200
CSV_FILE_PATH = os.path.expanduser(
    "~/Documents/GIT_repos/RP2040_BabyMonitoring/tools/rx_save_data/sensor_readings.csv"
)

BUFFER_SIZE = 30  # Average 30 readings (~30s - 1 min) into 1 entry
readings_buffer = []


def initialize_csv(file_path):
    """Ensures directory and CSV file with headers exist."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    if not os.path.exists(file_path):
        with open(file_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Time", "Measure", "Value", "Unit"])


def parse_sensor_block(block_text):
    """Robustly parses lines into: (Measure, Value, Unit)."""
    parsed_metrics = []
    lines = block_text.strip().split("\n")

    for line in lines:
        line = line.strip()
        if not line or ":" not in line or "Sensor Readings" in line:
            continue

        parts = line.split(":", 1)
        measure_raw = parts[0].strip()
        rest = parts[1].strip()

        # Extract numeric value (handles integers, floats)
        val_match = re.search(r"[-+]?\d*\.\d+|\d+", rest)
        if val_match:
            try:
                value = float(val_match.group())
                # Extract unit if present after the number
                unit_match = re.search(
                    r"(?:[0-9.]+\s*)([A-Za-z°%/-]+)", rest
                )
                unit = unit_match.group(1).strip() if unit_match else ""

                # Standardize metric names to eliminate mismatching
                measure = measure_raw
                if "co2" in measure.lower():
                    measure = "eCO2"
                elif "broadband" in measure.lower():
                    measure = "Broadband"
                elif "humidity" in measure.lower():
                    measure = "Humidity"

                parsed_metrics.append((measure, value, unit))
            except ValueError:
                continue

    return parsed_metrics


def flush_and_save_averages(buffer, file_path):
    """Computes arithmetic average across buffered measurements and appends to CSV."""
    if not buffer:
        return

    aggregated_data = {}

    for single_read in buffer:
        for measure, value, unit in single_read:
            if measure not in aggregated_data:
                aggregated_data[measure] = {"values": [], "unit": unit}
            aggregated_data[measure]["values"].append(value)
            if unit and not aggregated_data[measure]["unit"]:
                aggregated_data[measure]["unit"] = unit

    now = datetime.datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    rows_to_write = []
    for measure, details in aggregated_data.items():
        vals = details["values"]
        if vals:
            avg_val = round(sum(vals) / len(vals), 2)
            rows_to_write.append(
                [date_str, time_str, measure, avg_val, details["unit"]]
            )

    with open(file_path, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows_to_write)

    print(
        f"[{date_str} {time_str}] Averaged {len(buffer)} samples for {len(rows_to_write)} signals -> saved to CSV."
    )


def main():
    initialize_csv(CSV_FILE_PATH)
    print(f"Starting RP2040 Logger with {BUFFER_SIZE}-sample averaging...")

    while True:
        try:
            print(f"Connecting to {SERIAL_PORT}...")
            with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2) as ser:
                print("Serial connected!")
                current_block = []
                recording = False

                while True:
                    line = (
                        ser.readline().decode("utf-8", errors="ignore").strip()
                    )

                    if "--- Sensor Readings ---" in line:
                        if current_block and recording:
                            block_text = "\n".join(current_block)
                            parsed = parse_sensor_block(block_text)

                            if parsed:
                                readings_buffer.append(parsed)

                            if len(readings_buffer) >= BUFFER_SIZE:
                                flush_and_save_averages(
                                    readings_buffer, CSV_FILE_PATH
                                )
                                readings_buffer.clear()

                        current_block = []
                        recording = True
                    elif recording and line:
                        current_block.append(line)

        except (serial.SerialException, OSError) as e:
            print(f"Serial disconnected ({e}). Retrying in 3 seconds...")
            time.sleep(3)


if __name__ == "__main__":
    main()
