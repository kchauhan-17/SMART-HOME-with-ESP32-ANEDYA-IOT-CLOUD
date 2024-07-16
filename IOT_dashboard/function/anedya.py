import json
import requests
import time
import streamlit as st
import pandas as pd
import pytz

nodeId = "***" #node id
apiKey = "***" #api key


def anedya_config(NODE_ID, API_KEY):
    global nodeId, apiKey
    nodeId = NODE_ID
    apiKey = API_KEY


def anedya_sendCommand(COMMAND_NAME, COMMAND_DATA):
    url = "https://api.anedya.io/v1/commands/send"
    apiKey_in_format = "Bearer " + apiKey

    commandExpiry_time = int(time.time() + 518400) * 1000

    payload = json.dumps({
        "nodeid": nodeId,
        "command": COMMAND_NAME,
        "data": COMMAND_DATA,
        "type": "string",
        "expiry": commandExpiry_time,
    })
    headers = {"Content-Type": "application/json", "Authorization": apiKey_in_format}

    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()  # Raise an exception for 4xx or 5xx errors
    except requests.exceptions.RequestException as e:
        print(f"Error sending command: {e}")
        return None

    return response

def anedya_setValue(KEY, VALUE):
    url = "https://api.anedya.io/v1/valuestore/setValue"
    apiKey_in_format = "Bearer " + apiKey

    payload = json.dumps({
        "namespace": {
            "scope": "node",
            "id": nodeId
        },
        "key": KEY,
        "value": VALUE,
        "type": "boolean"
    })
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        "Authorization": apiKey_in_format
    }

    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()  # Raise an exception for 4xx or 5xx errors
        print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Error setting value: {e}")
        return None

    return response

def anedya_getValue(KEY):
    url = "https://api.anedya.io/v1/valuestore/getValue"
    apiKey_in_format = "Bearer " + apiKey

    payload = json.dumps({
        "namespace": {
            "scope": "node",
            "id": nodeId
        },
        "key": KEY
    })
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        "Authorization": apiKey_in_format
    }

    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()  # Raise an exception for 4xx or 5xx errors
        response_message = response.text
        print(response_message)
        error_code = json.loads(response_message).get("errorcode")
        if error_code == 0:
            data = json.loads(response_message).get("value")
            value = [data, 1]
        else:
            print(response_message)
            value = [False, -1]
    except requests.exceptions.RequestException as e:
        print(f"Error getting value: {e}")
        value = [False, -1]

    return value

def fetchHumidityData() -> pd.DataFrame:
    url = "https://api.anedya.io/v1/aggregates/variable/byTime"
    apiKey_in_formate = "Bearer " + apiKey

    currentTime = int(time.time())
    pastHour_Time = int(currentTime - 86400)

    payload = json.dumps(
        {
            "variable": "humidity",
            "from": pastHour_Time,
            "to": currentTime,
            "config": {
                "aggregation": {
                    "compute": "avg",
                    "forEachNode": True
                },
                "interval": {
                    "measure": "minute",
                    "interval": 5
                },
                "responseOptions": {
                    "timezone": "UTC"
                },
                "filter": {
                    "nodes": [
                        nodeId
                    ],
                    "type": "include"
                }
            }
        }
    )
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": apiKey_in_formate
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    response_message = response.text

    if response.status_code == 200:
        data_list = []

        response_data = json.loads(response_message).get("data")
        for timeStamp, value in reversed(response_data.items()):
            for entry in reversed(value):
                data_list.append(entry)

        if data_list:
            st.session_state.CurrentHumidity = round(data_list[0]["aggregate"], 2)
            df = pd.DataFrame(data_list)
            df["Datetime"] = pd.to_datetime(df["timestamp"], unit="s")
            local_tz = pytz.timezone("Asia/Kolkata")
            df["Datetime"] = df["Datetime"].dt.tz_localize("UTC").dt.tz_convert(local_tz)
            df.set_index("Datetime", inplace=True)
            df.drop(columns=["timestamp"], inplace=True)
            chart_data = df.reset_index()
        else:
            chart_data = pd.DataFrame()

        return chart_data
    else:
        st.write(response_message)
        return pd.DataFrame()



def fetchTemperatureData() -> pd.DataFrame:
    url = "https://api.anedya.io/v1/aggregates/variable/byTime"
    apiKey_in_formate = "Bearer " + apiKey

    currentTime = int(time.time())
    pastHour_Time = int(currentTime - 86400)

    payload = json.dumps(
        {
            "variable": "temperature",
            "from": pastHour_Time,
            "to": currentTime,
            "config": {
                "aggregation": {
                    "compute": "avg",
                    "forEachNode": True
                },
                "interval": {
                    "measure": "minute",
                    "interval": 5
                },
                "responseOptions": {
                    "timezone": "UTC"
                },
                "filter": {
                    "nodes": [
                        nodeId
                    ],
                    "type": "include"
                }
            }
        }
    )
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": apiKey_in_formate
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    response_message = response.text

    if response.status_code == 200:
        data_list = []

        response_data = json.loads(response_message).get("data")
        for timeStamp, value in reversed(response_data.items()):
            for entry in reversed(value):
                data_list.append(entry)

        if data_list:
            st.session_state.CurrentTemperature = round(data_list[0]["aggregate"], 2)
            df = pd.DataFrame(data_list)
            df["Datetime"] = pd.to_datetime(df["timestamp"], unit="s")
            local_tz = pytz.timezone("Asia/Kolkata")
            df["Datetime"] = df["Datetime"].dt.tz_localize("UTC").dt.tz_convert(local_tz)
            df.set_index("Datetime", inplace=True)
            df.drop(columns=["timestamp"], inplace=True)
            chart_data = df.reset_index()
        else:
            chart_data = pd.DataFrame()

        return chart_data
    else:
        st.write(response_message)
        return pd.DataFrame()