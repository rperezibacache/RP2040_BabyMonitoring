import os
import re
import subprocess
import time
import pandas as pd
import plotly.express as px
import streamlit as st

# Configuration & Paths
REMOTE_SSH_USER_HOST = "pi@192.168.0.70"
REMOTE_FILE_PATH = "/home/pi/Documents/GIT_repos/RP2040_BabyMonitoring/tools/rx_save_data/sensor_readings.csv"
LOCAL_DIR = "/home/ricardo/Documents/Personal/T_H_LCD_rp2040/tools/logs_plot/"
LOCAL_CSV_PATH = os.path.join(LOCAL_DIR, "sensor_readings.csv")

st.set_page_config(
    page_title="RP2040 Environmental Monitor",
    page_icon="🌡️",
    layout="wide",
)


def sync_remote_csv():
    """Syncs CSV log file from Raspberry Pi using rsync."""
    os.makedirs(LOCAL_DIR, exist_ok=True)
    remote_src = f"{REMOTE_SSH_USER_HOST}:{REMOTE_FILE_PATH}"
    try:
        result = subprocess.run(
            ["rsync", "-avz", "--update", remote_src, LOCAL_CSV_PATH],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return (
            (True, "Synced with Raspberry Pi.")
            if result.returncode == 0
            else (False, f"rsync Error: {result.stderr.strip()}")
        )
    except Exception as e:
        return False, f"rsync Exception: {str(e)}"


def clean_aqi_value(val_str):
    """Extracts integer value from AQI strings."""
    if pd.isna(val_str):
        return None
    match = re.search(r"(\d+)", str(val_str))
    return float(match.group(1)) if match else None


def get_ens160_aqi_status(aqi_val):
    """Returns status text and color icon based on ENS160 AQI rating."""
    try:
        val = int(aqi_val)
        if val in [1, 2]:
            return "Good", "🟢"
        elif val == 3:
            return "Moderate", "🟡"
        elif val == 4:
            return "Poor", "🟠"
        elif val >= 5:
            return "Unhealthy", "🔴"
    except (ValueError, TypeError):
        pass
    return "Unknown", "⚪"


def load_and_clean_data(file_path):
    """Reads and repairs CSV logs regardless of missing headers or truncated time values."""
    if not os.path.exists(file_path):
        return pd.DataFrame()

    try:
        # Step 1: Inspect raw file to check for header existence
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            first_line = f.readline().lower()

        # Step 2: Load dataframe with or without headers dynamically
        if "date" in first_line or "measure" in first_line:
            df = pd.read_csv(file_path)
        else:
            df = pd.read_csv(file_path, header=None)
            # Standardize columns for headerless CSVs
            cols = ["Date", "Time", "Measure", "Value", "Unit"]
            df = df.iloc[:, : len(cols)]  # Clip extra trailing columns
            df.columns = cols[: df.shape[1]]

        if df.empty:
            return pd.DataFrame()

        # Step 3: Strip whitespace from text columns
        for col in ["Date", "Time", "Measure"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()

        # Step 4: Map truncated/varying measure names to clean canonical names
        def normalize_measure(raw_name):
            n = raw_name.lower()
            if "temp" in n:
                return "Temperature"
            elif "hum" in n:
                return "Humidity"
            elif "aqi" in n:
                return "AQI"
            elif "tvoc" in n:
                return "TVOC"
            elif "eco2" in n or "co2" in n:
                return "eCO2"
            elif "broadband" in n:
                return "Broadband"
            elif "infrared" in n or "ir" in n:
                return "Infrared"
            return raw_name.strip()

        df["Measure"] = df["Measure"].apply(normalize_measure)

        # Drop invalid header duplicates or artifacts
        df = df[~df["Measure"].isin(["", "Measure", "nan", "None"])]

        # Clean AQI values if strings like "1 (1-5)" exist
        aqi_mask = df["Measure"] == "AQI"
        if aqi_mask.any():
            df.loc[aqi_mask, "Value"] = df.loc[aqi_mask, "Value"].apply(
                clean_aqi_value
            )

        # Step 5: Construct valid timestamps (handles HH:MM missing seconds)
        df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
        time_str = df["Time"].apply(
            lambda t: t if len(t.split(":")) == 3 else f"{t}:00"
        )
        df["Timestamp"] = pd.to_datetime(
            df["Date"] + " " + time_str, errors="coerce"
        )

        if "Unit" not in df.columns:
            df["Unit"] = ""

        return df.dropna(subset=["Timestamp", "Value"])

    except Exception as e:
        st.error(f"Error reading dataset: {e}")
        return pd.DataFrame()


def build_plotly_figure(signal_df, measure, height=300):
    """Generates an interactive Plotly graph for a given sensor signal."""
    unit_label = (
        signal_df["Unit"].iloc[-1]
        if not signal_df.empty and pd.notna(signal_df["Unit"].iloc[-1])
        else ""
    )
    y_label = f"{measure} ({unit_label})" if unit_label else measure

    fig = px.line(
        signal_df,
        x="Timestamp",
        y="Value",
        title=f"<b>{measure}</b>",
        labels={"Value": y_label, "Timestamp": "Time"},
        template="plotly_white",
    )

    if measure == "AQI":
        fig.update_yaxes(range=[0.8, 5.2], dtick=1)

    fig.update_traces(line_color="#1f77b4", line_width=2)
    fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        height=height,
        hovermode="x unified",
        uirevision=measure,
    )
    return fig


def main():
    st.title("👶 Emilio's Environmental Sensor Monitor")

    st.sidebar.header("⚙️ Dashboard Controls")
    live_update = st.sidebar.checkbox(
        "Enable Live Data Auto-Sync (1 min)", value=True
    )

    if live_update:
        rsync_success, rsync_msg = sync_remote_csv()
        if rsync_success:
            st.sidebar.success(rsync_msg)
        else:
            st.sidebar.warning(rsync_msg)

    df = load_and_clean_data(LOCAL_CSV_PATH)

    if df.empty:
        st.error(
            f"No valid sensor data parsed from `{LOCAL_CSV_PATH}`. Please verify file path or Raspberry Pi sync."
        )
        st.stop()

    st.sidebar.header("🔍 Historical Filters")
    min_date = df["Timestamp"].min().date()
    max_date = df["Timestamp"].max().date()

    selected_date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    if isinstance(selected_date_range, tuple) and len(selected_date_range) == 2:
        start_date, end_date = selected_date_range
        filtered_df = df[
            (df["Timestamp"].dt.date >= start_date)
            & (df["Timestamp"].dt.date <= end_date)
        ]
    else:
        filtered_df = df

    latest_timestamp = df["Timestamp"].max()
    st.caption(
        f"Last synced timestamp: **{latest_timestamp.strftime('%Y-%m-%d %H:%M:%S')}**"
    )

    # Extract single most recent value per metric
    latest_per_measure = (
        df.sort_values("Timestamp").groupby("Measure").last().reset_index()
    )
    measures = sorted(
        [str(m) for m in filtered_df["Measure"].unique() if pd.notna(m)]
    )

    # --- TOP KPI CARDS ---
    st.subheader("📊 Current Metrics")
    kpi_cols = st.columns(min(max(len(measures), 1), 7))
    for idx, measure in enumerate(measures):
        row = latest_per_measure[latest_per_measure["Measure"] == measure]
        col_target = kpi_cols[idx % len(kpi_cols)]

        if not row.empty:
            raw_val = row["Value"].values[0]

            if measure == "AQI":
                status, icon = get_ens160_aqi_status(raw_val)
                col_target.metric(
                    label="AQI",
                    value=f"{int(raw_val)}",
                    delta=f"{icon} {status}",
                    delta_color="normal",
                )
            else:
                unit = row["Unit"].values[0]
                unit_str = (
                    f" {unit}"
                    if pd.notna(unit) and str(unit).lower() != "nan"
                    else ""
                )
                col_target.metric(
                    label=measure, value=f"{raw_val:.2f}{unit_str}"
                )

    st.markdown("---")

    # --- INSPECTION MODE & PLOTS ---
    st.sidebar.header("🔬 Inspection Mode")
    inspect_measure = st.sidebar.selectbox(
        "Focus on Single Signal",
        options=["All Overview Grid"] + measures,
        index=0,
    )

    if inspect_measure != "All Overview Grid":
        st.subheader(f"🔍 Focused Inspection View: {inspect_measure}")
        signal_df = filtered_df[filtered_df["Measure"] == inspect_measure]
        fig = build_plotly_figure(signal_df, inspect_measure, height=500)
        st.plotly_chart(
            fig, use_container_width=True, key=f"focus_{inspect_measure}"
        )
    else:
        st.subheader("📈 Sensor Signal Plots")
        plot_cols = st.columns(2)

        for idx, measure in enumerate(measures):
            signal_df = filtered_df[filtered_df["Measure"] == measure]
            fig = build_plotly_figure(signal_df, measure, height=300)
            with plot_cols[idx % 2]:
                st.plotly_chart(
                    fig, use_container_width=True, key=f"grid_{measure}"
                )

    if live_update:
        time.sleep(60)
        st.rerun()


if __name__ == "__main__":
    main()
