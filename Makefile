# RP2040 LCD2004A + W5500 FreeRTOS Firmware
# Makefile wrapper around CMake

BUILD_DIR       := build
PICO_SDK_PATH   ?= $(HOME)/pico-sdk
FREERTOS_KERNEL_PATH ?= $(HOME)/FreeRTOS-Kernel
PORT            ?= /dev/ttyACM0
BAUD            ?= 115200

# Python venv for GUI tools
VENV_DIR        := tools/venv
PYTHON          := $(VENV_DIR)/bin/python3
PIP             := $(VENV_DIR)/bin/pip3
GUI_APP         := tools/serial_monitor.py

.PHONY: all clean flash monitor gui_run gui_setup configure

all: configure
	$(MAKE) -C $(BUILD_DIR) -j$(shell nproc)

configure:
	@mkdir -p $(BUILD_DIR)
	cd $(BUILD_DIR) && cmake .. \
		-DPICO_SDK_PATH=$(PICO_SDK_PATH) \
		-DFREERTOS_KERNEL_PATH=$(FREERTOS_KERNEL_PATH) \
		-DCMAKE_BUILD_TYPE=Release

clean:
	rm -rf $(BUILD_DIR)

flash: all
	picotool load $(BUILD_DIR)/firmware.uf2 -f
	picotool reboot

# Terminal serial monitor (picocom)
monitor:
	@which picocom >/dev/null 2>&1 || (echo "Install picocom: sudo apt install picocom" && exit 1)
	@echo "Opening $(PORT) at $(BAUD) baud... Press Ctrl+A then Ctrl+X to exit."
	picocom $(PORT) -b $(BAUD)

# --- Python venv + PyQt6 GUI ---

gui_setup:
	@echo "Creating Python venv at $(VENV_DIR)..."
	python3 -m venv $(VENV_DIR)
	@echo "Installing PyQt6 and pyserial into venv..."
	$(PIP) install --upgrade pip
	$(PIP) install PyQt6 pyserial
	@echo "GUI dependencies installed."

gui_run:
	@if [ ! -f "$(PYTHON)" ]; then \
		echo "Venv not found. Running 'make gui_setup' first..."; \
		$(MAKE) gui_setup; \
	fi
	@echo "Launching Serial Monitor GUI..."
	$(PYTHON) $(GUI_APP) &