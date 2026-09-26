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

# Buffer settings
BUFFER_SIZE = 30  # Number of complete reading blocks to aggregate before logging
readings_buffer = []


def initialize_csv(file_path):
    """Ensures directory and CSV file with headers exist."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    if not os.path.exists(file_path):
        with open(file_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Time", "Measure", "Value", "Unit"])


def parse_sensor_block(block_text):
    """Parses a raw serial text block into a list of tuples: (Measure, Value, Unit)."""
    parsed_metrics = []
    lines = block_text.strip().split("\n")

    for line in lines:
        # Match lines formatted as: "Measure: Value Unit" or "AQI: 3 (1-5)"
        match = re.search(
            r"([A-Za-z0-9_\s]+):\s*([0-9.]+)\s*([A-Za-z0-9°%/-]*)", line
        )
        if match:
            measure = match.group(1).strip()
            value = float(match.group(2))
            unit = match.group(3).strip()
            parsed_metrics.append((measure, value, unit))

    return parsed_metrics


def flush_and_save_averages(buffer, file_path):
    """Computes the arithmetic average across the 30 buffered measurements and appends to CSV."""
    if not buffer:
        return

    # Group values and units by measure: { 'Temperature': {'values': [...], 'unit': '°C'} }
    aggregated_data = {}

    for single_read in buffer:
        for measure, value, unit in single_read:
            if measure not in aggregated_data:
                aggregated_data[measure] = {"values": [], "unit": unit}
            aggregated_data[measure]["values"].append(value)

    # Use current Pi time for the averaged record
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

    # Append averaged rows to CSV
    with open(file_path, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows_to_write)

    print(
        f"[{date_str} {time_str}] Successfully averaged and wrote {len(buffer)} readings to CSV."
    )


def main():
    initialize_csv(CSV_FILE_PATH)
    print(f"Starting RP2040 Logger with {BUFFER_SIZE}-sample averaging...")

    while True:
        try:
            print(f"Opening serial connection on {SERIAL_PORT}...")
            with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2) as ser:
                print("Serial connected! Listening for incoming sensor data...")

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
                                print(
                                    f"Buffered sample {len(readings_buffer)}/{BUFFER_SIZE}"
                                )

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
            print(f"Serial port disconnected ({e}). Retrying in 3 seconds...")
            time.sleep(3)


if __name__ == "__main__":
    main()
