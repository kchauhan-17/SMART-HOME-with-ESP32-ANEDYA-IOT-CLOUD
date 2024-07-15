# SMART-HOME-with-ESP32-ANEDYA-IOT-CLOUD
In this smart home setup, lighting is managed via a user-friendly Streamlit dashboard, allowing remote control and automation. The dashboard also displays real-time temperature and humidity data from integrated sensors like the DHT11, enhancing comfort and efficiency through informed environmental insights.


## **Hardware Components:**
- ESP32 board; 
- DHT11 sensor; 
- 2 LEDs; 
- Resistors (appropriate values for LEDs, typically 220Ω) (optinal); 
- Breadboard and jumper wires;

## **Connection Details:**
- DHT11 Sensor: Data to D5, VCC to 3.3V, GND to GND.; 
- LED1: Anode to D4 through a resistor, Cathode to GND.; 
- LED2: Anode to D18 through a resistor, Cathode to GND.

## **📊 Data evaluation template**
A simple Streamlit app showing how to evaluate and annotate data, using dataframes and charts.

Open in Streamlit

How to run it on your own machine
Install the requirements

**$ pip install -r requirements.txt**

Run the app

**$ streamlit run streamlit_app.py**
