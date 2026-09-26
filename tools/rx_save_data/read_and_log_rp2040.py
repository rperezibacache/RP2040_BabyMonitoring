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

BUFFER_SIZE = 30  # Number of reading blocks to average before saving
readings_buffer = []


def initialize_csv(file_path):
    """Ensures CSV directory and headers exist."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    if not os.path.exists(file_path):
        with open(file_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Time", "Measure", "Value", "Unit"])


def parse_sensor_block(block_text):
    """Parses multi-metric lines delimited by '|' or newlines."""
    parsed_metrics = []

    # Clean app prefixes like '[15:02:37] Received:' if passed through
    block_text = re.sub(
        r"\[\d{2}:\d{2}:\d{2}\]\s*Received:\s*", "", block_text, flags=re.IGNORECASE
    )

    # Split lines into individual key-value pairs separated by '|' or '\n'
    raw_chunks = re.split(r"[\n|]", block_text)

    for chunk in raw_chunks:
        chunk = chunk.strip()
        if not chunk or ":" not in chunk or "Sensor Readings" in chunk:
            continue

        parts = chunk.split(":", 1)
        raw_label = parts[0].strip()
        rest = parts[1].strip()

        # Extract numeric value
        val_match = re.search(r"[-+]?\d*\.\d+|\d+", rest)
        if not val_match:
            continue

        try:
            value = float(val_match.group())

            # Canonical mapping for metric names
            label_lower = raw_label.lower()
            if "temp" in label_lower:
                measure = "Temperature"
                unit = "°C"
            elif "hum" in label_lower:
                measure = "Humidity"
                unit = "%"
            elif "aqi" in label_lower:
                measure = "AQI"
                unit = ""
            elif "tvoc" in label_lower:
                measure = "TVOC"
                unit = "ppb"
            elif "eco2" in label_lower:
                measure = "eCO2"
                unit = "ppm"
            elif "broadband" in label_lower:
                measure = "Broadband"
                unit = "lux"
            elif "infrared" in label_lower:
                measure = "Infrared"
                unit = "lux"
            else:
                measure = raw_label
                # Extract unit fallback
                unit_match = re.search(
                    r"[A-Za-z°%/-]+", rest[val_match.end() :]
                )
                unit = unit_match.group().strip() if unit_match else ""

            parsed_metrics.append((measure, value, unit))
        except ValueError:
            continue

    return parsed_metrics


def flush_and_save_averages(buffer, file_path):
    """Calculates average across buffered reads and appends to CSV."""
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
        f"[{date_str} {time_str}] Successfully saved {len(rows_to_write)} metrics to CSV (Averaged {len(buffer)} frames)."
    )


def main():
    initialize_csv(CSV_FILE_PATH)
    print("Starting RP2040 Serial Reader...")

    while True:
        try:
            with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2) as ser:
                print(f"Connected to {SERIAL_PORT}!")
                current_block = []
                recording = False

                while True:
                    raw_line = (
                        ser.readline().decode("utf-8", errors="ignore").strip()
                    )

                    # Strip timestamp tag if app inserts it
                    line = re.sub(
                        r"\[\d{2}:\d{2}:\d{2}\]\s*Received:\s*",
                        "",
                        raw_line,
                        flags=re.IGNORECASE,
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
