ADB := adb
DEVICE_ID := S4CUZDHMOR955LEY
VENV := .venv/bin/activate
STREAMLIT := .venv/bin/streamlit

.PHONY: all check-device optimize start-media dashboard run stop-gui restore-gui help

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
	@echo "Starting screen keepalive loop..."
	@nohup bash -c "while true; do $(ADB) shell input keyevent KEYCODE_WAKEUP; $(ADB) shell input swipe 500 500 505 505 10; sleep 2; done" > /dev/null 2>&1 &
	@echo "Restarting go2rtc media server..."
	@pkill go2rtc || true
	@sleep 1
	@go2rtc -c go2rtc.yaml > /dev/null 2>&1 &
	@sleep 2

dashboard:
	@echo "Launching Streamlit dashboard..."
	@DISPLAY="" $(STREAMLIT) run app.py --server.headless true --server.port 8501

run: start-media dashboard
