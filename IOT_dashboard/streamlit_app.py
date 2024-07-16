import streamlit as st
import pandas as pd
import altair as alt
import requests 
from streamlit_autorefresh import st_autorefresh

from function.anedya import anedya_config
from function.anedya import anedya_sendCommand
from function.anedya import anedya_getValue
from function.anedya import anedya_setValue
from function.anedya import fetchHumidityData
from function.anedya import fetchTemperatureData

nodeId = "*************"  # get it from anedya dashboard -> project -> node 
apiKey = "****************"  # anedya project apikey

st.set_page_config(page_title="SMART HOME", layout="wide")

# Uncomment to enable autorefresh
count = st_autorefresh(interval=1000, limit=None, key="auto-refresh-handler")

# --------------- HELPER FUNCTIONS -----------------------

def V_SPACE(lines):
    for _ in range(lines):
        st.write("&nbsp;")

humidityData = pd.DataFrame()
temperatureData = pd.DataFrame()

def main():
    anedya_config(nodeId, apiKey)
    global humidityData, temperatureData

    # Initialize the log in state if does not exist
    if "LoggedIn" not in st.session_state:
        st.session_state.LoggedIn = False

    if "LED1ButtonText" not in st.session_state:
        st.session_state.LED1ButtonText = " LED 1 On!"

    if "LED2ButtonText" not in st.session_state:
        st.session_state.LED2ButtonText = " LED 2 On!"

    if "LED1State" not in st.session_state:
        st.session_state.LED1State = False

    if "LED2State" not in st.session_state:
        st.session_state.LED2State = False

    if "CurrentHumidity" not in st.session_state:
        st.session_state.CurrentHumidity = 0

    if "CurrentTemperature" not in st.session_state:
        st.session_state.CurrentTemperature = 0

    if st.session_state.LoggedIn is False:
        drawLogin()
    else:
        humidityData = fetchHumidityData()
        temperatureData = fetchTemperatureData()

        GetLED1Status()
        GetLED2Status()

        drawDashboard()

def drawLogin():
    cols = st.columns([1, 0.8, 1], gap='small')
    with cols[0]:
        pass
    with cols[1]:
        st.markdown("<h1 style='color: navy;'>SMART HOME</h1>", unsafe_allow_html=True)
        username_inp = st.text_input("Username")
        password_inp = st.text_input("Password", type="password")
        submit_button = st.button(label="Submit")

        if submit_button:
            if username_inp == "admin" and password_inp == "admin":
                st.session_state.LoggedIn = True
                st.rerun()
            else:
                st.error("Invalid Credential!")
    with cols[2]:
        print()

def drawDashboard():
    headercols = st.columns([1, 0.1, 0.1], gap="small")
    with headercols[0]:
        st.markdown("<h1 style='color: navy;'>SMART HOME Dashboard</h1>", unsafe_allow_html=True)
    with headercols[1]:
        st.button("Refresh")
    with headercols[2]:
        logout = st.button("Logout")

    if logout:
        st.session_state.LoggedIn = False
        st.rerun()

    st.markdown("<p style='color: navy;'>This dashboard provides a Smart homme Data information , also allowing you to control the LEDs !</p>", unsafe_allow_html=True)

    st.subheader(body="Current Status", anchor=False)
    cols = st.columns(2, gap="medium")
    with cols[0]:
        st.metric(label="Humidity", value=str(st.session_state.CurrentHumidity) + " %")
    with cols[1]:
        st.metric(label="Temperature", value=str(st.session_state.CurrentTemperature) + "  °C")

    buttons = st.columns(2, gap="small")
    with buttons[0]:
        st.text("Control LED 1:")
        st.button(label=st.session_state.LED1ButtonText, on_click=operateLED1)
    with buttons[1]:
        st.text("Control LED 2:")
        st.button(label=st.session_state.LED2ButtonText, on_click=operateLED2)

    charts = st.columns(2, gap="small")
    with charts[0]:
        st.subheader(body="Humidity", anchor=False)
        if humidityData.empty:
            st.write("No Data Available!")
        else:
            humidity_chart_an = alt.Chart(data=humidityData).mark_area(
                line={'color': '#1fa22f'},
                color=alt.Gradient(
                    gradient='linear',
                    stops=[alt.GradientStop(color='#1fa22f', offset=1),
                        alt.GradientStop(color='rgba(255,255,255,0)', offset=0)],
                    x1=1,
                    x2=1,
                    y1=1,
                    y2=0,
                ),
                interpolate='monotone',
                cursor='crosshair'
            ).encode(
                x=alt.X(
                    shorthand="Datetime:T",
                    axis=alt.Axis(format="%Y-%m-%d %H:%M:%S", title="Datetime", tickCount=10, grid=True, tickMinStep=5),
                ),  # T indicates temporal (time-based) data
                y=alt.Y(
                    "aggregate:Q",
                    scale=alt.Scale(domain=[20, 100]),
                    axis=alt.Axis(title="Humidity (%)", grid=True, tickCount=10),
                ),  # Q indicates quantitative data
                tooltip=[alt.Tooltip('Datetime:T', format="%Y-%m-%d %H:%M:%S", title="Time",),
                        alt.Tooltip('aggregate:Q', format="0.2f", title="Value")],
            ).properties(height=400).interactive()

            # Display the Altair chart using Streamlit
            st.altair_chart(humidity_chart_an, use_container_width=True)

    with charts[1]:
        st.subheader(body="Temperature", anchor=False)
        if temperatureData.empty:
            st.write("No Data Available!")
        else:
            temperature_chart_an = alt.Chart(data=temperatureData).mark_area(
                line={'color': '#1fa22f'},
                color=alt.Gradient(
                    gradient='linear',
                    stops=[alt.GradientStop(color='#1fa22f', offset=1),
                        alt.GradientStop(color='rgba(255,255,255,0)', offset=0)],
                    x1=1,
                    x2=1,
                    y1=1,
                    y2=0,
                ),
                interpolate='monotone',
                cursor='crosshair'
            ).encode(
                x=alt.X(
                    shorthand="Datetime:T",
                    axis=alt.Axis(format="%Y-%m-%d %H:%M:%S", title="Datetime", tickCount=10, grid=True, tickMinStep=5),
                ),  # T indicates temporal (time-based) data
                y=alt.Y(
                    "aggregate:Q",
                    # scale=alt.Scale(domain=[0, 100]),
                    scale=alt.Scale(zero=False, domain=[10, 50]),
                    axis=alt.Axis(title="Temperature (°C)", grid=True, tickCount=10),
                ),  # Q indicates quantitative data
                tooltip=[alt.Tooltip('Datetime:T', format="%Y-%m-%d %H:%M:%S", title="Time",),
                        alt.Tooltip('aggregate:Q', format="0.2f", title="Value")],
            ).properties(height=400).interactive()

            st.altair_chart(temperature_chart_an, use_container_width=True)

def operateLED1():
    if st.session_state.LED1State is False:
        anedya_sendCommand("LED1", "ON")
        anedya_setValue("LED1", True)
        st.session_state.LED1ButtonText = "LED 1 Off!"
        st.session_state.LED1State = True
        st.toast("LED 1 on!")
    else:
        st.session_state.LED1ButtonText = "LED 1 On!"
        st.session_state.LED1State = False
        anedya_sendCommand("LED1", "OFF")
        anedya_setValue("LED1", False)
        st.toast("LED 1 off!")

def operateLED2():
    if st.session_state.LED2State is False:
        anedya_sendCommand("LED2", "ON")
        anedya_setValue("LED2", True)
        st.session_state.LED2ButtonText = "LED 2 Off!"
        st.session_state.LED2State = True
        st.toast("LED 2 on!")
    else:
        st.session_state.LED2ButtonText = "LED 2 On!"
        st.session_state.LED2State = False
        anedya_sendCommand("LED2", "OFF")
        anedya_setValue("LED2", False)
        st.toast("LED 2 off!")

@st.cache_data(ttl=4, show_spinner=False)
def GetLED1Status() -> list:
    value = anedya_getValue("LED1")
    if value[1] == 1:
        on = value[0]
        if on:
            st.session_state.LED1State = True
            st.session_state.LED1ButtonText = "LED 1 Off!"
        else:
            st.session_state.LED1State = False
            st.session_state.LED1ButtonText = "LED 1 On!"
    return value

@st.cache_data(ttl=4, show_spinner=False)
def GetLED2Status() -> list:
    value = anedya_getValue("LED2")
    if value[1] == 1:
        on = value[0]
        if on:
            st.session_state.LED2State = True
            st.session_state.LED2ButtonText = "LED 2 Off!"
        else:
            st.session_state.LED2State = False
            st.session_state.LED2ButtonText = "LED 2 On!"
    return value

if __name__ == "__main__":
    main()