ADB := adb
DEVICE_ID := S4CUZDHMOR955LEY
VENV_STREAMLIT := /home/pi/Documents/GIT_repos/RP2040_BabyMonitoring/tools/Xiomi_CamSound/.venv/bin/streamlit
PWD := $(shell pwd)

.PHONY: all check-device optimize start-media dashboard run stop help

all: check-device optimize

check-device:
	@echo "Checking ADB connection for device $(DEVICE_ID)..."
	@$(ADB) devices | grep -q "$(DEVICE_ID).*device" || \
		(echo "Error: Device $(DEVICE_ID) not found or unauthorized." && exit 1)
	@echo "Device $(DEVICE_ID) connected successfully."

optimize: check-device
	@echo "Applying CPU performance & power settings..."
	@$(ADB) shell settings put global stay_on_while_plugged_in 3
	@$(ADB) shell settings put global low_power 0
	@$(ADB) shell dumpsys deviceidle disable

start-media: check-device
	@echo "Ensuring IP Webcam port forwarding over USB..."
	-@$(ADB) forward tcp:8080 tcp:8080
	@echo "Starting ADB screen keepalive loop..."
	@nohup bash -c "while true; do $(ADB) shell input keyevent KEYCODE_WAKEUP; $(ADB) shell input swipe 500 500 505 505 10; sleep 2; done" > /dev/null 2>&1 &
	@echo "Force-stopping old media processes..."
	-@pkill -9 go2rtc || true
	-@pkill -9 screenrecord || true
	@sleep 1
	@echo "Starting go2rtc media server..."
	@go2rtc -c $(PWD)/go2rtc.yaml > /dev/null 2>&1 &
	@sleep 2

dashboard:
	@echo "Launching Environmental Monitor Streamlit Dashboard..."
	-@pkill -f "streamlit run _telemetry_main.py" || true
	@$(VENV_STREAMLIT) run _telemetry_main.py \
		--server.headless true \
		--server.address 0.0.0.0 \
		--server.port 8501 \
		--browser.gatherUsageStats false

run: start-media dashboard

stop:
	@echo "Stopping all background streaming and dashboard processes..."
	-@pkill -9 go2rtc || true
	-@pkill -9 screenrecord || true
	-@pkill -f "streamlit run _telemetry_main.py" || true
	-@pkill -f "input keyevent KEYCODE_WAKEUP" || true
	@echo "Processes terminated."

help:
	@echo "Available commands:"
	@echo "  make run         - Optimize device, start go2rtc media stream, and launch dashboard"
	@echo "  make dashboard   - Run Streamlit telemetry dashboard directly"
	@echo "  make start-media - Launch background keepalive and go2rtc instance"
	@echo "  make stop        - Terminate go2rtc, Streamlit, and background loops"
