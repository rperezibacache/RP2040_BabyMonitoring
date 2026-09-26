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

BUFFER_SIZE = 30
readings_buffer = []


def initialize_csv(file_path):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    if not os.path.exists(file_path):
        with open(file_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Time", "Measure", "Value", "Unit"])


def parse_sensor_block(block_text):
    parsed_metrics = []
    lines = block_text.strip().split("\n")

    for line in lines:
        line = line.strip()
        if not line or ":" not in line or "Sensor Readings" in line:
            continue

        parts = line.split(":", 1)
        raw_measure = parts[0].strip()
        rest = parts[1].strip()

        val_match = re.search(r"[-+]?\d*\.\d+|\d+", rest)
        if val_match:
            try:
                value = float(val_match.group())

                # Standardize metric names
                measure_lower = raw_measure.lower()
                if "co2" in measure_lower:
                    measure = "eCO2"
                elif "hum" in measure_lower:
                    measure = "Humidity"
                elif "temp" in measure_lower:
                    measure = "Temperature"
                elif "aqi" in measure_lower:
                    measure = "AQI"
                elif "broadband" in measure_lower:
                    measure = "Broadband"
                elif "tvoc" in measure_lower:
                    measure = "TVOC"
                else:
                    measure = raw_measure

                unit_match = re.search(r"[A-Za-z°%/-]+", rest[val_match.end() :])
                unit = unit_match.group().strip() if unit_match else ""

                parsed_metrics.append((measure, value, unit))
            except ValueError:
                continue

    return parsed_metrics


def flush_and_save_averages(buffer, file_path):
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
        f"[{date_str} {time_str}] Logged {len(rows_to_write)} signals ({BUFFER_SIZE} samples averaged)."
    )


def main():
    initialize_csv(CSV_FILE_PATH)
    print("Starting RP2040 Logger...")

    while True:
        try:
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
            print(f"Serial dropped ({e}). Reconnecting in 3s...")
            time.sleep(3)


if __name__ == "__main__":
    main()
