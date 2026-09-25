import csv
import os
import re
import time
import serial
import serial.tools.list_ports

CSV_FILENAME = "sensor_readings.csv"


def find_rp2040_port():
    """Auto-detect the serial port for the RP2040/Raspberry Pi Pico."""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if "ttyACM" in port.device or "ttyUSB" in port.device:
            return port.device
    return None


def initialize_csv(filename):
    """Ensure the CSV file exists and has header columns."""
    file_exists = os.path.exists(filename)
    with open(filename, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # Write headers if file is being newly created
        if not file_exists:
            writer.writerow(["Date", "Time", "Measure", "Value", "Unit"])


def log_readings_to_csv(filename, raw_block):
    """Parse a full sensor readings block and append entries to the CSV."""
    current_date = time.strftime("%Y-%m-%d")
    current_time = time.strftime("%H:%M:%S")

    # Regex patterns to extract each key, numerical value, and optional unit
    # Matches patterns like 'Temperature: 25.33 °C' or 'AQI: 3 (1-5)'
    patterns = [
        (r"Temperature:\s*([\d\.]+)\s*(°C|C)", "Temperature"),
        (r"Humidity:\s*([\d\.]+)\s*(%)", "Humidity"),
        (r"AQI:\s*(\d+)", "AQI"),
        (r"TVOC:\s*(\d+)\s*(ppb)", "TVOC"),
        (r"eCO2:\s*(\d+)\s*(ppm)", "eCO2"),
        (r"Broadband \(Visible \+ IR\):\s*(\d+)", "Broadband (Visible + IR)"),
        (r"Infrared:\s*(\d+)", "Infrared"),
    ]

    extracted_rows = []

    for pattern, measure_name in patterns:
        match = re.search(pattern, raw_block)
        if match:
            value = match.group(1)
            # Check if unit was captured in group 2
            unit = match.group(2) if len(match.groups()) > 1 else ""
            extracted_rows.append(
                [current_date, current_time, measure_name, value, unit]
            )

    if extracted_rows:
        with open(filename, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(extracted_rows)
        print(
            f"[{current_time}] Saved block ({len(extracted_rows)} metrics) to {filename}"
        )


def main():
    port_name = find_rp2040_port() or "/dev/ttyACM0"
    baud_rate = 115200

    initialize_csv(CSV_FILENAME)
    print(f"Connecting to RP2040 on {port_name}...")
    print(f"Appending readings to '{CSV_FILENAME}'\n")

    try:
        ser = serial.Serial(port=port_name, baudrate=baud_rate, timeout=2.0)
        ser.reset_input_buffer()

        block_buffer = []

        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode("utf-8", errors="replace").rstrip()

                # Print live output to terminal
                timestamp = time.strftime("%H:%M:%S")
                print(f"[{timestamp}] Received: {line}")

                # Accumulate block text
                if "--- Sensor Readings ---" in line:
                    # Parse the previous accumulated block if present
                    if block_buffer:
                        full_block = "\n".join(block_buffer)
                        log_readings_to_csv(CSV_FILENAME, full_block)
                        block_buffer = []

                block_buffer.append(line)

            time.sleep(0.01)

    except serial.SerialException as e:
        print(f"\n[Error] Could not open port {port_name}: {e}")
    except KeyboardInterrupt:
        print("\nProgram stopped by user.")
    finally:
        if "ser" in locals() and ser.is_open:
            ser.close()


if __name__ == "__main__":
    main()
