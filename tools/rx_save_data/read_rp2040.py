import time
import serial
import serial.tools.list_ports


def find_rp2040_port():
    """Auto-detect the serial port for the RP2040/Raspberry Pi Pico."""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        # Check standard Linux device patterns for USB CDC devices
        if "ttyACM" in port.device or "ttyUSB" in port.device:
            return port.device
    return None


def main():
    # 1. Detect port automatically or fallback to /dev/ttyACM0
    port_name = find_rp2040_port() or "/dev/ttyACM0"
    baud_rate = 115200  # RP2040 USB CDC ignores baud rate, but 115200 is standard

    print(f"Connecting to RP2040 on {port_name}...")

    try:
        # 2. Open serial connection
        ser = serial.Serial(port=port_name, baudrate=baud_rate, timeout=2.0)

        # Clear buffer to start fresh
        ser.reset_input_buffer()
        print("Connected! Listening for data (Press Ctrl+C to stop)...\n")

        # 3. Read loop
        while True:
            if ser.in_waiting > 0:
                # Read a full line, decode bytes to UTF-8, and strip trailing newlines
                line = ser.readline().decode("utf-8", errors="replace").rstrip()

                # Print received data with a local timestamp
                timestamp = time.strftime("%H:%M:%S")
                print(f"[{timestamp}] Received: {line}")

            time.sleep(0.01)  # Brief delay to reduce CPU usage

    except serial.SerialException as e:
        print(f"\n[Error] Could not open or read port {port_name}: {e}")
        print("Tip: Check if another application (e.g., minicom) is currently using the port.")
    except KeyboardInterrupt:
        print("\nProgram stopped by user.")
    finally:
        if "ser" in locals() and ser.is_open:
            ser.close()
            print("Serial connection closed.")


if __name__ == "__main__":
    main()
