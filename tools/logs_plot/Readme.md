```markdown
# 👶 RP2040 Environmental Baby Monitor & Dashboard

An end-to-end IoT monitoring solution that reads real-time environmental metrics (Temperature, Humidity, AQI, TVOC, eCO2, Light) from an **RP2040 microcontroller**, streams data to a local **Raspberry Pi**, and renders an interactive **Streamlit analytics dashboard** with automated SSH syncing.

---

## 📌 Project Overview


```

[ RP2040 Microcontroller ]
│
│ Serial Port (/dev/ttyACM0)
▼
[ Raspberry Pi Receiver ] ──(Saves to CSV)──► sensor_readings.csv
│
│ SCP Auto-Sync (5s)
▼
[ Streamlit Dashboard ]

```

1. **Edge Acquisition:** The RP2040 microcontroller measures environmental parameters once per second and formats them over USB CDC Serial.
2. **Local Logging:** A persistent Python logger on the Raspberry Pi captures serial lines, parses metrics, and appends structured records to `sensor_readings.csv`.
3. **Automated Sync:** A remote Streamlit dashboard uses background `scp` over SSH every 5 seconds to pull the latest dataset seamlessly.
4. **Interactive Dashboard:** Visualizes live KPI cards, individual signal trend plots, ENS160 Air Quality color-coded status badges, and inspection views with zoom capabilities.

---

## 📊 Measured Parameters & Hardware

| Sensor Metric | Description | Unit / Scale |
| :--- | :--- | :--- |
| **Temperature** | Ambient Room Temperature | °C |
| **Humidity** | Relative Humidity | % |
| **AQI (ENS160)** | Air Quality Index | 1 (Good) to 5 (Unhealthy) |
| **TVOC** | Total Volatile Organic Compounds | ppb |
| **eCO2** | Equivalent Carbon Dioxide | ppm |
| **Broadband** | Visible + Infrared Light Level | Lux / Raw |
| **Infrared** | Infrared Light Spectrum | Lux / Raw |

---

## 🚀 System Setup & Execution

### Step 1: Passwordless SSH Setup (Raspberry Pi ➔ PC)
The dashboard syncs the CSV using background `scp`. Set up passwordless SSH authentication once from your host PC to your Raspberry Pi:

```bash
# 1. Generate SSH key (if not already done)
ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519

# 2. Copy public key to your Raspberry Pi
ssh-copy-id pi@192.168.0.70

# 3. Verify you can connect without a password prompt
ssh pi@192.168.0.70

```

---

### Step 2: Raspberry Pi Data Logger

1. **Connect RP2040** to the Raspberry Pi via USB.
2. **Grant Serial Permissions:**
```bash
sudo usermod -aG dialout $USER

```


*(Log out and log back in for changes to apply).*
3. **Install Logger Dependencies:**
```bash
pip install pyserial

```


4. **Run the Serial Logger Script:**
```bash
python3 ~/Documents/GIT_repos/RP2040_BabyMonitoring/tools/rx_save_data/read_and_log_rp2040.py

```



---

### Step 3: Host PC Dashboard

1. **Install Dashboard Dependencies:**
```bash
pip install streamlit pandas plotly

```


2. **Launch the Streamlit App:**
```bash
python3 -m streamlit run monitor_dashboard.py

```


*The application will open automatically in your browser at `http://localhost:8501`.*

---

## 🔄 How Data Transfer Works

1. **Serial Ingestion:** The script on the Raspberry Pi monitors `/dev/ttyACM0` at `115200 baud`. When a block starting with `--- Sensor Readings ---` is detected, it parses values via regular expressions and appends them to:
```
~/Documents/GIT_repos/RP2040_BabyMonitoring/tools/rx_save_data/sensor_readings.csv

```


2. **Data Structure (`sensor_readings.csv`):**
```csv
Date,Time,Measure,Value,Unit
2026-09-25,14:06:22,Temperature,25.33,°C
2026-09-25,14:06:22,Humidity,51.29,%
2026-09-25,14:06:22,AQI,3,
2026-09-25,14:06:22,TVOC,464,ppb
2026-09-25,14:06:22,eCO2,855,ppm

```


3. **Dashboard Sync & Visualization:**
* The dashboard runs `scp pi@192.168.0.70:... /local/path/` every 5 seconds.
* `clean_aqi_value()` extracts pure integer values for AQI (stripping index text like `(1-5)`).
* Metric statuses update dynamically with ENS160 datasheet standards:
* 🟢 **AQI 1-2:** Good
* 🟡 **AQI 3:** Moderate
* 🟠 **AQI 4:** Poor
* 🔴 **AQI 5:** Unhealthy





---

## 💡 Usage & Troubleshooting Tips

* **Zooming & Analyzing Signal Spikes:** Uncheck **"Enable Live Data Auto-Sync"** in the sidebar to pause background reruns while zooming into historical graphs.
* **Single Signal Focus Mode:** Select a metric from the **"Focus on Single Signal"** dropdown in the sidebar to inspect a full-screen high-resolution view.
* **Date Range Filtering:** Use the calendar date picker in the sidebar to narrow down historical sensor trends.

```

```
