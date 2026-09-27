import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Raspberry Pi Live Monitor",
    layout="wide"
)

st.title("📹 Live Environmental & Video Stream Dashboard")

col_video, col_status = st.columns([2, 1])

with col_video:
    st.subheader("Redmi 9A WebRTC Feed (Sub-100ms Latency)")

    go2rtc_url = "http://192.168.0.70:1984/stream.html?src=redmi_cam&mode=webrtc"

    # CSS transform rotates the iframe 90deg without overloading the Pi CPU
    components.html(
        f"""
        <div style="width:100%; height:480px; background-color:#000; border-radius:10px; overflow:hidden; display:flex; justify-content:center; align-items:center;">
            <iframe 
                src="{go2rtc_url}" 
                style="width:480px; height:100%; border:none; transform: rotate(90deg);" 
                allow="autoplay; camera; microphone; fullscreen; speaker; display-capture">
            </iframe>
        </div>
        """,
        height=500,
    )

with col_status:
    st.subheader("System Status")
    st.success("WebRTC Media Server Active (Port 1984)")
    st.info("Audio Codec: OPUS")

    st.metric(label="Temperature", value="23.5 °C")
    st.metric(label="Humidity", value="48.2 %")
    st.metric(label="AQI", value="12")

st.markdown("---")

