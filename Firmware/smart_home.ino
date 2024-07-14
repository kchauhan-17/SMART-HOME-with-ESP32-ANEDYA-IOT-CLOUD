#include <Arduino.h>
#include <WiFi.h>             
#include <PubSubClient.h>     
#include <WiFiClientSecure.h> 
#include <ArduinoJson.h>      
#include <TimeLib.h>          
#include <DHT.h>              // Include the DHT sensor library

#define DHTPIN 5     // Define the DHT sensor pin (GPIO 5)
#define DHTTYPE DHT11 // Define the DHT sensor type (DHT11)

// DHT sensor initialization
DHT dht(DHTPIN, DHTTYPE);

String regionCode = "ap-in-1";                   
const char *deviceID = "dc064093-33b6-4888-a485-00b6ec1b0427"; 
const char *connectionkey = "0c413337dbd57c211eed883899ef196c";  
const char *ssid = "Khushi";     
const char *pass = "khushi1702"; 

const char *mqtt_broker = "mqtt.ap-in-1.anedya.io";                      
const char *mqtt_username = deviceID;                                      
const char *mqtt_password = connectionkey;                                 
const int mqtt_port = 8883;                                                
String responseTopic = "$anedya/device/" + String(deviceID) + "/response"; 
String errorTopic = "$anedya/device/" + String(deviceID) + "/errors";      
String commandTopic = "$anedya/device/" + String(deviceID) + "/commands";  

const char *ca_cert = R"EOF(                           
-----BEGIN CERTIFICATE-----
MIICDDCCAbOgAwIBAgITQxd3Dqj4u/74GrImxc0M4EbUvDAKBggqhkjOPQQDAjBL
MQswCQYDVQQGEwJJTjEQMA4GA1UECBMHR3VqYXJhdDEPMA0GA1UEChMGQW5lZHlh
MRkwFwYDVQQDExBBbmVkeWEgUm9vdCBDQSAzMB4XDTI0MDEwMTAwMDAwMFoXDTQz
MTIzMTIzNTk1OVowSzELMAkGA1UEBhMCSU4xEDAOBgNVBAgTB0d1amFyYXQxDzAN
BgNVBAoTBkFuZWR5YTEZMBcGA1UEAxMQQW5lZHlhIFJvb3QgQ0EgMzBZMBMGByqG
SM49AgEGCCqGSM49AwEHA0IABKsxf0vpbjShIOIGweak0/meIYS0AmXaujinCjFk
BFShcaf2MdMeYBPPFwz4p5I8KOCopgshSTUFRCXiiKwgYPKjdjB0MA8GA1UdEwEB
/wQFMAMBAf8wHQYDVR0OBBYEFNz1PBRXdRsYQNVsd3eYVNdRDcH4MB8GA1UdIwQY
MBaAFNz1PBRXdRsYQNVsd3eYVNdRDcH4MA4GA1UdDwEB/wQEAwIBhjARBgNVHSAE
CjAIMAYGBFUdIAAwCgYIKoZIzj0EAwIDRwAwRAIgR/rWSG8+L4XtFLces0JYS7bY
5NH1diiFk54/E5xmSaICIEYYbhvjrdR0GVLjoay6gFspiRZ7GtDDr9xF91WbsK0P
-----END CERTIFICATE-----
)EOF";

String statusTopic = "$anedya/device/" + String(deviceID) + "/commands/updateStatus/json"; 
String timeRes, commandId;                                                                 
String led1Status = "off";                                                                 
String led2Status = "off";                                                                 
long long responseTimer = 0;                                                               
bool processCheck = false;                                                                 

const int ledPin1 = 4; 
const int ledPin2 = 18; 

// Variables for DHT data
float temperature = 0.0;
float humidity = 0.0;

// Function Declarations
void connectToMQTT();                                               
void mqttCallback(char *topic, byte *payload, unsigned int length); 
void setDevice_time();                                              

WiFiClientSecure esp_client;
PubSubClient mqtt_client(esp_client);

void setup()
{
  Serial.begin(115200); 
  delay(1500);          

  WiFi.begin(ssid, pass);
  Serial.println();
  Serial.print("Connecting to WiFi...");
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("Connected, IP address: ");
  Serial.println(WiFi.localIP());

  esp_client.setCACert(ca_cert);                 
  mqtt_client.setServer(mqtt_broker, mqtt_port); 
  mqtt_client.setKeepAlive(60);                  
  mqtt_client.setCallback(mqttCallback);         
  connectToMQTT();                               
  mqtt_client.subscribe(responseTopic.c_str());  
  mqtt_client.subscribe(errorTopic.c_str());     
  mqtt_client.subscribe(commandTopic.c_str());   

  setDevice_time(); 

  pinMode(ledPin1, OUTPUT);
  pinMode(ledPin2, OUTPUT);

  dht.begin(); // Initialize the DHT sensor
}

void loop()
{
  if (!mqtt_client.connected())
  {
    connectToMQTT();
  }
  if (millis() - responseTimer > 700 && processCheck && commandId != "")
  {
    String statusProcessingPayload = "{\"reqId\": \"\",\"commandId\": \"" + commandId + "\",\"status\": \"processing\",\"ackdata\": \"\",\"ackdatatype\": \"\"}";
    mqtt_client.publish(statusTopic.c_str(), statusProcessingPayload.c_str());
    processCheck = false;
  }
  else if (millis() - responseTimer >= 1000 && commandId != "")
  {
    if (led1Status == "on" || led1Status == "ON")
    {
      digitalWrite(ledPin1, HIGH);
      Serial.println("Led 1 ON");
    }
    else if (led1Status == "off" || led1Status == "OFF")
    {
      digitalWrite(ledPin1, LOW);
      Serial.println("Led 1 OFF");
    }

    if (led2Status == "on" || led2Status == "ON")
    {
      digitalWrite(ledPin2, HIGH);
      Serial.println("Led 2 ON");
    }
    else if (led2Status == "off" || led2Status == "OFF")
    {
      digitalWrite(ledPin2, LOW);
      Serial.println("Led 2 OFF");
    }

    String statusSuccessPayload = "{\"reqId\": \"\",\"commandId\": \"" + commandId + "\",\"status\": \"success\",\"ackdata\": \"\",\"ackdatatype\": \"\"}";
    mqtt_client.publish(statusTopic.c_str(), statusSuccessPayload.c_str());

    commandId = ""; 
  }

  // Read and publish DHT sensor data every 1 seconds
  static unsigned long lastDHTUpdateTime = 0;
  if (millis() - lastDHTUpdateTime > 1000)
  {
    lastDHTUpdateTime = millis();
    temperature = dht.readTemperature();
    humidity = dht.readHumidity();

    if (isnan(temperature) || isnan(humidity))
    {
      Serial.println("Failed to read from DHT sensor!");
    }
    else
    {
      Serial.print("Temperature: ");
      Serial.print(temperature);
      Serial.print(" °C, Humidity: ");
      Serial.print(humidity);
      Serial.println(" %");

      // Publish temperature data
      String tempPayload = "{\"variableIdentifier\": \"temperature\",\"value\": " + String(temperature) + "}";
      mqtt_client.publish(responseTopic.c_str(), tempPayload.c_str());

      // Publish humidity data
      String humidityPayload = "{\"variableIdentifier\": \"humidity\",\"value\": " + String(humidity) + "}";
      mqtt_client.publish(responseTopic.c_str(), humidityPayload.c_str());
    }
  }

  mqtt_client.loop();
}

void connectToMQTT()
{
  while (!mqtt_client.connected())
  {
    const char *client_id = deviceID;       
    Serial.print("Connecting to Anedya Broker....... ");
    if (mqtt_client.connect(client_id, mqtt_username, mqtt_password)) 
    {
      Serial.println("Connected to Anedya broker");
    }
    else
    {
      Serial.print("Failed to connect to Anedya broker, rc=");
      Serial.print(mqtt_client.state());
      Serial.println(" Retrying in 5 seconds.");
      delay(5000);
    }
  }
}

void mqttCallback(char *topic, byte *payload, unsigned int length)
{
  char res[150] = "";
  for (unsigned int i = 0; i < length; i++)
  {
    res[i] = payload[i];
  }
  String str_res = String(res); // Properly initialize the str_res variable

  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  Serial.println(str_res);

  StaticJsonDocument<200> Response;
  DeserializationError error = deserializeJson(Response, str_res);
  if (error)
  {
    Serial.print("deserializeJson() failed: ");
    Serial.println(error.c_str());
    return;
  }

  if (Response.containsKey("deviceSendTime"))
  {
    timeRes = str_res;
  }
  else if (Response.containsKey("command"))
  {
    String command = Response["command"];
    if (command == "LED1")
    {
      led1Status = Response["data"].as<String>();
    }
    else if (command == "LED2")
    {
      led2Status = Response["data"].as<String>();
    }

    responseTimer = millis();
    commandId = Response["commandId"].as<String>();
    String statusReceivedPayload = "{\"reqId\": \"\",\"commandId\": \"" + commandId + "\",\"status\": \"received\",\"ackdata\": \"\",\"ackdatatype\": \"\"}";
    mqtt_client.publish(statusTopic.c_str(), statusReceivedPayload.c_str());
    processCheck = true;
  }
  else if (Response.containsKey("errCode") && Response["errCode"].as<String>() != "0")
  {
    Serial.println(str_res);
  }
}

void setDevice_time()
{
  String timeTopic = "$anedya/device/" + String(deviceID) + "/time/json"; 
  const char *mqtt_topic = timeTopic.c_str();

  if (mqtt_client.connected())
  {
    Serial.print("Time synchronizing......");

    boolean timeCheck = true;
    long long deviceSendTime;
    long long timeTimer = millis();
    while (timeCheck)
    {
      mqtt_client.loop();

      unsigned int iterate = 2000;
      if (millis() - timeTimer >= iterate)
      {
        Serial.print(".");
        timeTimer = millis();
        deviceSendTime = millis();

        StaticJsonDocument<200> requestPayload; 
        requestPayload["deviceSendTime"] = deviceSendTime;
        String jsonPayload;
        serializeJson(requestPayload, jsonPayload);
        const char *jsonPayloadLiteral = jsonPayload.c_str();
        mqtt_client.publish(mqtt_topic, jsonPayloadLiteral);
      }

      if (timeRes != "")
      {
        String strResTime(timeRes);

        DynamicJsonDocument jsonResponse(100);
        deserializeJson(jsonResponse, strResTime);

        long long serverReceiveTime = jsonResponse["serverReceiveTime"];
        long long serverSendTime = jsonResponse["serverSendTime"];

        long long deviceRecTime = millis();
        long long currentTime = (serverReceiveTime + serverSendTime + deviceRecTime - deviceSendTime) / 2;
        long long currentTimeSeconds = currentTime / 1000;

        setTime(currentTimeSeconds);
        Serial.println("\n synchronized!");
        timeCheck = false;
      }
    }
  }
  else
  {
    connectToMQTT();
  }
}