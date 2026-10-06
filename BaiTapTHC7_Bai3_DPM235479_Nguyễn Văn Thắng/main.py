import network
import time
from machine import Pin, PWM
from umqtt.simple import MQTTClient

# Khởi tạo PWM điều khiển Servo tại GPIO 13 (chu kỳ 50Hz)
servo = PWM(Pin(13), freq=50)

def set_angle(angle):
    if angle < 0: angle = 0
    if angle > 180: angle = 180
    # Chuẩn xung SG90: 0 độ = 500.000 ns (0.5ms), 180 độ = 2.400.000 ns (2.4ms)
    pulse_ns = int(500000 + (angle / 180) * (2400000 - 500000))
    servo.duty_ns(pulse_ns)

# Đặt góc ban đầu 90 độ
set_angle(90)

# Cấu hình WiFi và Adafruit IO
WIFI_SSID = "Wokwi-GUEST"
WIFI_PASSWORD = ""
MQTT_BROKER = "io.adafruit.com"
MQTT_PORT = 1883
MQTT_USER = "ndhuy412"
MQTT_PASSWORD = "YOUR_AIO_KEY"
MQTT_TOPIC = "ndhuy412/feeds/servo-control"
CLIENT_ID = "ESP32_Servo_Subscriber"

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Dang ket noi WiFi...", end="")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        while not wlan.isconnected():
            print(".", end="")
            time.sleep(0.2)
    print("\nWiFi da ket noi! IP:", wlan.ifconfig()[0])

def on_message(topic, msg):
    try:
        payload = msg.decode("utf-8")
        angle = int(float(payload))
        print(">> Nhan lenh tu Web qua MQTT: Goc =", angle, "do")
        set_angle(angle)
    except Exception as e:
        print("Loi nhan lenh:", e)

def connect_mqtt():
    client = MQTTClient(
        client_id=CLIENT_ID,
        server=MQTT_BROKER,
        port=MQTT_PORT,
        user=MQTT_USER,
        password=MQTT_PASSWORD,
        keepalive=60
    )
    client.set_callback(on_message)
    print("Dang ket noi MQTT...")
    client.connect()
    client.subscribe(MQTT_TOPIC)
    print("Subscribed topic", MQTT_TOPIC, "thanh cong!")
    return client

connect_wifi()
client = connect_mqtt()

while True:
    try:
        client.check_msg()
    except Exception as e:
        try:
            client = connect_mqtt()
        except:
            pass
    time.sleep(0.05)