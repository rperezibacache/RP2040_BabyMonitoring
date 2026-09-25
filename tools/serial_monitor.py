#!/usr/bin/env python3
"""
PyQt6 Serial Monitor for RP2040 USB CDC
Displays printf output from the Pico firmware.
"""

import sys
import serial
import serial.tools.list_ports
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QTextEdit, QSpinBox,
    QStatusBar, QMessageBox, QGroupBox
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont, QTextCursor


class SerialReaderThread(QThread):
    data_received = pyqtSignal(str)
    disconnected = pyqtSignal(str)

    def __init__(self, port: str, baudrate: int):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.running = False
        self.ser = None

    def run(self):
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.1
            )
            self.running = True
            while self.running:
                try:
                    if self.ser.in_waiting > 0:
                        data = self.ser.read(self.ser.in_waiting)
                        try:
                            text = data.decode('utf-8', errors='replace')
                        except UnicodeDecodeError:
                            text = data.decode('latin-1', errors='replace')
                        self.data_received.emit(text)
                except serial.SerialException as e:
                    self.disconnected.emit(str(e))
                    break
        except serial.SerialException as e:
            self.disconnected.emit(str(e))

    def stop(self):
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.wait(500)


class SerialMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RP2040 Serial Monitor")
        self.setGeometry(100, 100, 900, 600)

        self.reader_thread = None

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        # --- Connection Controls ---
        conn_group = QGroupBox("Connection")
        conn_layout = QHBoxLayout(conn_group)

        # Port selector
        conn_layout.addWidget(QLabel("Port:"))
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(180)
        conn_layout.addWidget(self.port_combo)

        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setFixedWidth(80)
        self.refresh_btn.clicked.connect(self.refresh_ports)
        conn_layout.addWidget(self.refresh_btn)

        # Baud rate
        conn_layout.addWidget(QLabel("Baud:"))
        self.baud_spin = QSpinBox()
        self.baud_spin.setRange(300, 3000000)
        self.baud_spin.setValue(115200)
        self.baud_spin.setSingleStep(1200)
        self.baud_spin.setSuffix(" baud")
        conn_layout.addWidget(self.baud_spin)

        # Connect / Disconnect
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setFixedWidth(100)
        self.connect_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.connect_btn.clicked.connect(self.toggle_connection)
        conn_layout.addWidget(self.connect_btn)

        conn_layout.addStretch()
        layout.addWidget(conn_group)

        # --- Output Display ---
        output_group = QGroupBox("Serial Output")
        output_layout = QVBoxLayout(output_group)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("JetBrains Mono", 10))
        self.output_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 6px;
            }
        """)
        output_layout.addWidget(self.output_text)

        # Output controls
        out_btn_layout = QHBoxLayout()
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.output_text.clear)
        out_btn_layout.addWidget(self.clear_btn)

        self.autoscroll_check = QPushButton("Auto-scroll: ON")
        self.autoscroll_check.setCheckable(True)
        self.autoscroll_check.setChecked(True)
        self.autoscroll_check.clicked.connect(self.toggle_autoscroll)
        out_btn_layout.addWidget(self.autoscroll_check)

        self.timestamp_check = QPushButton("Timestamps: OFF")
        self.timestamp_check.setCheckable(True)
        self.timestamp_check.setChecked(False)
        self.timestamp_check.clicked.connect(self.toggle_timestamps)
        out_btn_layout.addWidget(self.timestamp_check)

        out_btn_layout.addStretch()
        output_layout.addLayout(out_btn_layout)
        layout.addWidget(output_group, stretch=1)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Disconnected")

        # NOW refresh ports — status_bar exists
        self.refresh_ports()

    def refresh_ports(self):
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        for p in sorted(ports, key=lambda x: x.device):
            desc = f"{p.device} — {p.description}" if p.description else p.device
            self.port_combo.addItem(desc, p.device)
        if self.port_combo.count() == 0:
            self.port_combo.addItem("No ports found", "")
        self.status_bar.showMessage(f"Found {self.port_combo.count()} port(s)")

    def toggle_connection(self):
        if self.reader_thread and self.reader_thread.isRunning():
            self.disconnect_port()
        else:
            self.connect_port()

    def connect_port(self):
        port = self.port_combo.currentData()
        if not port:
            QMessageBox.warning(self, "No Port", "Please select a serial port.")
            return

        baud = self.baud_spin.value()

        self.reader_thread = SerialReaderThread(port, baud)
        self.reader_thread.data_received.connect(self.append_data)
        self.reader_thread.disconnected.connect(self.on_disconnect)
        self.reader_thread.start()

        self.connect_btn.setText("Disconnect")
        self.connect_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        self.port_combo.setEnabled(False)
        self.baud_spin.setEnabled(False)
        self.status_bar.showMessage(f"Connected to {port} @ {baud} baud")

    def disconnect_port(self):
        if self.reader_thread:
            self.reader_thread.stop()
            self.reader_thread = None

        self.connect_btn.setText("Connect")
        self.connect_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.port_combo.setEnabled(True)
        self.baud_spin.setEnabled(True)
        self.status_bar.showMessage("Disconnected")

    def on_disconnect(self, reason: str):
        self.disconnect_port()
        self.status_bar.showMessage(f"Disconnected: {reason}")

    def append_data(self, text: str):
        cursor = self.output_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        if self.timestamp_check.isChecked() and not text.startswith('\n'):
            import datetime
            ts = datetime.datetime.now().strftime("[%H:%M:%S.%f")[:-3] + "] "
            text = ts + text.replace("\n", "\n" + ts)

        cursor.insertText(text)
        if self.autoscroll_check.isChecked():
            self.output_text.setTextCursor(cursor)
            self.output_text.ensureCursorVisible()

    def toggle_autoscroll(self):
        if self.autoscroll_check.isChecked():
            self.autoscroll_check.setText("Auto-scroll: ON")
        else:
            self.autoscroll_check.setText("Auto-scroll: OFF")

    def toggle_timestamps(self):
        if self.timestamp_check.isChecked():
            self.timestamp_check.setText("Timestamps: ON")
        else:
            self.timestamp_check.setText("Timestamps: OFF")

    def closeEvent(self, event):
        if self.reader_thread and self.reader_thread.isRunning():
            self.reader_thread.stop()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = SerialMonitor()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()