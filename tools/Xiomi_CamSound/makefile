# ==============================================================================
# Makefile: Redmi 9A Headless Optimization & Direct Operations via ADB
# ==============================================================================

ADB := adb
DEVICE_ID := S4CUZDHMOR955LEY

.PHONY: all check-device optimize high-perf disable-bloat limits stop-gui kill-backgrounds restore-gui help

# Default target
all: check-device optimize

## Verify device connectivity
check-device:
	@echo "Checking ADB connection for device $(DEVICE_ID)..."
	@$(ADB) devices | grep -q "$(DEVICE_ID).*device" || \
		(echo "Error: Device $(DEVICE_ID) not found or unauthorized. Run 'adb devices' to check." && exit 1)
	@echo "Device $(DEVICE_ID) connected successfully."

## Run complete headless optimization suite
optimize: check-device high-perf disable-bloat limits stop-gui kill-backgrounds
	@echo "\n=== Redmi 9A successfully optimized for headless streaming! ==="

## 1. Configure CPU High-Performance & Disable Power Saver
high-perf:
	@echo "Configuring CPU performance and power settings..."
	$(ADB) shell settings put global stay_on_while_plugged_in 3
	$(ADB) shell settings put global low_power 0
	$(ADB) shell dumpsys deviceidle disable

## 2. Disable Unnecessary Apps & MIUI Bloatware
disable-bloat:
	@echo "Disabling background bloatware and cloud services..."
	-$(ADB) shell pm disable-user --user 0 com.miui.analytics
	-$(ADB) shell pm disable-user --user 0 com.xiaomi.mipushesmsservice
	-$(ADB) shell pm disable-user --user 0 com.miui.cloudservice
	-$(ADB) shell pm disable-user --user 0 com.miui.cloudbackup
	-$(ADB) shell pm disable-user --user 0 com.google.android.youtube
	-$(ADB) shell pm disable-user --user 0 com.android.chrome
	-$(ADB) shell pm disable-user --user 0 com.google.android.apps.docs
	-$(ADB) shell pm disable-user --user 0 com.google.android.gm

## 3. Zero System Animations & Restrict Process Limits
limits:
	@echo "Disabling animations and capping hidden background processes..."
	$(ADB) shell settings put global max_hidden_apps 2
	$(ADB) shell settings put global window_animation_scale 0.0
	$(ADB) shell settings put global transition_animation_scale 0.0
	$(ADB) shell settings put global animator_duration_scale 0.0

## 4. Stop GUI & MIUI Launcher Stack (Headless Mode)
stop-gui:
	@echo "Stopping MIUI Home Launcher and System UI..."
	-$(ADB) shell am force-stop com.miui.home
	-$(ADB) shell am force-stop com.android.systemui

## 5. Kill Cached Background Processes
kill-backgrounds:
	@echo "Killing remaining cached background processes..."
	$(ADB) shell am kill-all

## Restore standard Android UI / Launcher
restore-gui:
	@echo "Restoring MIUI Home Launcher..."
	$(ADB) shell am start -n com.miui.home/.launcher.Launcher

## Display available commands
help:
	@echo "Available Makefile targets:"
	@echo "  make optimize          - Run full headless performance optimization"
	@echo "  make check-device      - Verify ADB connectivity"
	@echo "  make high-perf         - Prevent sleeping & set maximum CPU availability"
	@echo "  make disable-bloat     - Disable background Xiaomi/Google bloatware"
	@echo "  make limits            - Zero system animation scales and limit RAM usage"
	@echo "  make stop-gui          - Stop Launcher and System UI (headless mode)"
	@echo "  make kill-backgrounds  - Purge cached apps from system memory"
	@echo "  make restore-gui       - Restart MIUI Home GUI"
