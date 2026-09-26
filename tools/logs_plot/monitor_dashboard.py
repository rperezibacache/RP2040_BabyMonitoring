import os
import re
import subprocess
import time
import pandas as pd
import plotly.express as px
import streamlit as st

# File Paths & Remote SSH Configuration
REMOTE_SSH_USER_HOST = "pi@192.168.0.70"
REMOTE_FILE_PATH = "/home/pi/Documents/GIT_repos/RP2040_BabyMonitoring/tools/rx_save_data/sensor_readings.csv"
LOCAL_DIR = "/home/ricardo/Documents/Personal/T_H_LCD_rp2040/tools/logs_plot/"
LOCAL_CSV_PATH = os.path.join(LOCAL_DIR, "sensor_readings.csv")

st.set_page_config(
    page_title="RP2040 Sensor Monitoring Dashboard",
    page_icon="🌡️",
    layout="wide",
)


def sync_remote_csv():
    """Synchronizes sensor_readings.csv from Pi using rsync."""
    os.makedirs(LOCAL_DIR, exist_ok=True)
    remote_src = f"{REMOTE_SSH_USER_HOST}:{REMOTE_FILE_PATH}"

    try:
        result = subprocess.run(
            ["rsync", "-avz", "--update", remote_src, LOCAL_CSV_PATH],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return True, "Successfully synchronized with Pi (rsync)."
        else:
            return False, f"rsync Error: {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return False, "rsync connection timed out."
    except Exception as e:
        return False, f"rsync Exception: {str(e)}"


def clean_aqi_value(val_str):
    """Extracts numerical digits from strings like '3 (1-5)'."""
    if pd.isna(val_str):
        return None
    match = re.search(r"(\d+)", str(val_str))
    if match:
        return float(match.group(1))
    return None


def get_ens160_aqi_status(aqi_val):
    """Categorizes ENS160 AQI (1-5)."""
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
    """Loads CSV, strips whitespace from Measure names, and parses timestamps."""
    if not os.path.exists(file_path):
        return pd.DataFrame()

    try:
        df = pd.read_csv(file_path)
        if df.empty or "Measure" not in df.columns:
            return pd.DataFrame()

        # Crucial Fix: Strip leading/trailing spaces from Measure column
        df["Measure"] = df["Measure"].astype(str).str.strip()

        # Normalize common measure name variations
        df["Measure"] = df["Measure"].replace(
            {
                "eco2": "eCO2",
                "eCO2 ": "eCO2",
                "humidity": "Humidity",
                "broadband": "Broadband",
            }
        )

        aqi_mask = df["Measure"] == "AQI"
        if aqi_mask.any():
            df.loc[aqi_mask, "Value"] = df.loc[aqi_mask, "Value"].apply(
                clean_aqi_value
            )

        df["Timestamp"] = pd.to_datetime(
            df["Date"].astype(str) + " " + df["Time"].astype(str),
            errors="coerce",
        )
        df["Value"] = pd.to_numeric(df["Value"], errors="coerce")

        return df.dropna(subset=["Timestamp", "Value"])
    except Exception:
        return pd.DataFrame()


def build_plotly_figure(signal_df, measure, height=300):
    """Constructs Plotly chart for a single metric."""
    unit_label = (
        signal_df["Unit"].iloc[0]
        if not signal_df.empty and pd.notna(signal_df["Unit"].iloc[0])
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
    st.title("👶 RP2040 Environmental Sensor Monitor")

    st.sidebar.header("⚙️ Dashboard Controls")
    live_update = st.sidebar.checkbox(
        "Enable Live Data Auto-Sync (1 min)",
        value=True,
        help="Uncheck to lock the zoom level while analyzing.",
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
            f"No data available at `{LOCAL_CSV_PATH}`. Check SSH credentials or remote file path."
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

    # Use data from the latest timestamp block
    latest_df = df[df["Timestamp"] == latest_timestamp]
    measures = sorted(filtered_df["Measure"].unique().tolist())

    # --- TOP KPI CARDS ---
    kpi_cols = st.columns(min(max(len(measures), 1), 6))
    for idx, measure in enumerate(measures):
        measure_data = latest_df[latest_df["Measure"] == measure]
        col_target = kpi_cols[idx % len(kpi_cols)]

        if not measure_data.empty:
            raw_val = measure_data["Value"].values[0]

            if measure == "AQI":
                status, icon = get_ens160_aqi_status(raw_val)
                col_target.metric(
                    label="Air Quality Index (AQI)",
                    value=f"{int(raw_val)}",
                    delta=f"{icon} {status}",
                    delta_color="normal",
                )
            else:
                unit = measure_data["Unit"].values[0]
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
