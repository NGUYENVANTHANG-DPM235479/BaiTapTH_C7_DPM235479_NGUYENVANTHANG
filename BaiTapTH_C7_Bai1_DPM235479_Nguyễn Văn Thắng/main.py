import network
import time
import urequests
from machine import ADC, Pin

SSID = "Wokwi-GUEST"
PASSWORD = ""

API_KEY = "2AURIHK32H1KEA3A"

pot = ADC(Pin(34))

pot.atten(ADC.ATTN_11DB)
pot.width(ADC.WIDTH_12BIT)


def connect_wifi():

    print()
    print("==============================")
    print(" ESP32 MICROPYTHON")
    print(" THINGSPEAK")
    print("==============================")

    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)

    if not wifi.isconnected():

        print("Dang ket noi WiFi...")

        wifi.connect(SSID, PASSWORD)

        timeout = 20

        while not wifi.isconnected() and timeout > 0:

            print(".", end="")
            time.sleep(1)

            timeout -= 1

    print()

    if wifi.isconnected():

        print("WiFi da ket noi!")

        print("IP:", wifi.ifconfig()[0])

        return wifi

    else:

        print("Khong ket noi duoc WiFi!")

        return None


wifi = connect_wifi()



while True:


    if wifi is None or not wifi.isconnected():

        print()
        print("WiFi bi mat ket noi!")

        wifi = connect_wifi()

        time.sleep(2)

        continue



    value = pot.read()

    print()
    print("------------------------------")
    print("Gia tri bien tro:", value)



    url = (
        "http://api.thingspeak.com/update"
        "?api_key=" + API_KEY +
        "&field1=" + str(value)
    )

    print("Dang gui du lieu...")
    print(url)




    try:

        response = urequests.get(url)

        print("HTTP Status:", response.status_code)

        data = response.text

        print("ThingSpeak tra ve:", data)

        if response.status_code == 200 and data != "0":

            print(">>> GUI DU LIEU THANH CONG!")

            print(">>> Entry ID:", data)

        else:

            print(">>> GUI DU LIEU THAT BAI!")

        response.close()


    except Exception as e:

        print("Loi khi gui ThingSpeak:")
        print(e)



    print("Cho 15 giay de gui lan tiep...")

    time.sleep(15)