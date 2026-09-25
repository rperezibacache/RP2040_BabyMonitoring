import os
import re
import subprocess
import time
import pandas as pd
import plotly.express as px
import streamlit as st

# File Paths & SCP Configuration
REMOTE_SCP_PATH = "pi@192.168.0.70:~/Documents/GIT_repos/RP2040_BabyMonitoring/tools/rx_save_data/sensor_readings.csv"
LOCAL_DIR = "/home/ricardo/Documents/Personal/T_H_LCD_rp2040/tools/logs_plot/"
LOCAL_CSV_PATH = os.path.join(LOCAL_DIR, "sensor_readings.csv")

st.set_page_config(
    page_title="RP2040 Sensor Monitoring Dashboard",
    page_icon="🌡️",
    layout="wide",
)


def fetch_remote_csv():
    """Executes scp to pull the latest sensor_readings.csv from the remote Raspberry Pi."""
    os.makedirs(LOCAL_DIR, exist_ok=True)
    try:
        result = subprocess.run(
            ["scp", REMOTE_SCP_PATH, LOCAL_DIR],
            capture_output=True,
            text=True,
            timeout=4,
        )
        if result.returncode == 0:
            return True, "Successfully synced with Pi."
        else:
            return False, f"SCP Error: {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return False, "SCP connection timed out."
    except Exception as e:
        return False, f"SCP Exception: {str(e)}"


def clean_aqi_value(val_str):
    """Extracts only numerical digits from strings like '3 (1-5)'."""
    if pd.isna(val_str):
        return None
    match = re.search(r"(\d+)", str(val_str))
    if match:
        return float(match.group(1))
    return None


def get_ens160_aqi_status(aqi_val):
    """Categorizes ENS160 AQI (1-5) according to official datasheet specs."""
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
    """Loads CSV and cleans numerical values including AQI parsing."""
    if not os.path.exists(file_path):
        return pd.DataFrame()

    try:
        df = pd.read_csv(file_path)
        if df.empty:
            return df

        aqi_mask = df["Measure"] == "AQI"
        if aqi_mask.any():
            df.loc[aqi_mask, "Value"] = df.loc[aqi_mask, "Value"].apply(
                clean_aqi_value
            )

        df["Timestamp"] = pd.to_datetime(
            df["Date"] + " " + df["Time"], errors="coerce"
        )
        df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
        return df.dropna(subset=["Timestamp", "Value"])
    except Exception:
        return pd.DataFrame()


def build_plotly_figure(signal_df, measure, height=300):
    """Constructs a standardized Plotly chart for a single sensor metric."""
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
        uirevision=measure,  # Keeps zoom/pan position consistent during reruns
    )
    return fig


def main():
    st.title("👶 RP2040 Environmental Sensor Monitor")

    # --- SIDEBAR CONTROLS ---
    st.sidebar.header("⚙️ Dashboard Controls")

    # Master Toggle to pause live updates while analyzing/zooming
    live_update = st.sidebar.checkbox(
        "Enable Live Data Auto-Sync (5s)",
        value=True,
        help="Uncheck this box to freeze live updates while inspecting or zooming into graphs.",
    )

    # Fetch data on demand or continuously based on toggle
    if live_update:
        scp_success, scp_msg = fetch_remote_csv()
        if scp_success:
            st.sidebar.success(scp_msg)
        else:
            st.sidebar.warning(scp_msg)

    df = load_and_clean_data(LOCAL_CSV_PATH)

    if df.empty:
        st.error(
            f"No data available at `{LOCAL_CSV_PATH}`. Check SSH credentials or remote file path."
        )
        st.stop()

    # --- HISTORICAL FILTER ---
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

    # --- TOP KPI CARDS ---
    latest_timestamp = df["Timestamp"].max()
    st.caption(
        f"Last synced timestamp: **{latest_timestamp.strftime('%Y-%m-%d %H:%M:%S')}**"
    )

    latest_df = df[df["Timestamp"] == latest_timestamp]
    measures = sorted(df["Measure"].unique().tolist())

    kpi_cols = st.columns(min(len(measures), 5))
    for idx, measure in enumerate(measures):
        measure_data = latest_df[latest_df["Measure"] == measure]
        if not measure_data.empty:
            raw_val = measure_data["Value"].values[0]
            col_target = kpi_cols[idx % 5]

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
                    f" {unit}" if pd.notna(unit) and str(unit) != "nan" else ""
                )
                col_target.metric(label=measure, value=f"{raw_val}{unit_str}")

    st.markdown("---")

    # --- DETAILED INSPECTION MODE ---
    st.sidebar.header("🔬 Inspection Mode")
    inspect_measure = st.sidebar.selectbox(
        "Focus on Single Signal",
        options=["All Overview Grid"] + measures,
        index=0,
    )

    if inspect_measure != "All Overview Grid":
        st.subheader(f"🔍 Focused Inspection View: {inspect_measure}")
        st.info(
            "💡 Tip: Uncheck 'Enable Live Data Auto-Sync' in the sidebar to lock the zoom level while analyzing."
        )

        signal_df = filtered_df[filtered_df["Measure"] == inspect_measure]
        fig = build_plotly_figure(signal_df, inspect_measure, height=500)
        st.plotly_chart(
            fig, use_container_width=True, key=f"focus_{inspect_measure}"
        )

    else:
        # --- OVERVIEW 2-COLUMN GRID ---
        st.subheader("📈 Sensor Signal Plots")
        plot_cols = st.columns(2)

        for idx, measure in enumerate(measures):
            signal_df = filtered_df[filtered_df["Measure"] == measure]
            fig = build_plotly_figure(signal_df, measure, height=300)

            with plot_cols[idx % 2]:
                st.plotly_chart(
                    fig, use_container_width=True, key=f"grid_{measure}"
                )

    # Handle loop delay manually to avoid wiping out browser DOM events
    if live_update:
        time.sleep(5)
        st.rerun()


if __name__ == "__main__":
    main()
