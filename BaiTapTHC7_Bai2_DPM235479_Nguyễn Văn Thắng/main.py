from machine import Pin, PWM
import network
import urequests
import time

# ===== LỚP ĐIỀU KHIỂN SERVO =====
class Servo:
    """Lớp điều khiển Servo bằng PWM trên ESP32"""
    
    def __init__(self, pin_number):
        """Khởi tạo servo trên chân GPIO chỉ định"""
        self.pwm = PWM(Pin(pin_number), freq=50)  # Servo hoạt động ở 50Hz
        self.pwm.duty(77)  # Vị trí giữa (90°) ban đầu
    
    def write(self, angle):
        """
        Quay servo đến góc chỉ định (0 - 180 độ)
        Chuyển đổi góc → duty cycle:
          0°   → 0.5ms pulse → duty ≈ 26
          90°  → 1.5ms pulse → duty ≈ 77  
          180° → 2.5ms pulse → duty ≈ 128
        """
        # Giới hạn góc trong khoảng 0-180
        angle = max(0, min(180, angle))
        # Tính duty cycle (10-bit: 0-1023)
        duty = int(26 + (angle / 180) * (128 - 26))
        self.pwm.duty(duty)

# ===== CẤU HÌNH WIFI =====
WIFI_SSID = "Wokwi-GUEST"    # WiFi mặc định của Wokwi (kết nối internet thật)
WIFI_PASS = ""                 # Không cần mật khẩu

# ===== CẤU HÌNH THINGSPEAK =====
# ⚠️ THAY API KEY CỦA BẠN VÀO ĐÂY!
WRITE_API_KEY = "0818FSHOB1FV422P"
THINGSPEAK_URL = "http://api.thingspeak.com/update"

# ===== CẤU HÌNH SERVO =====
SERVO_LEFT_PIN = 13     # Servo trái - chân GPIO 13
SERVO_RIGHT_PIN = 14    # Servo phải - chân GPIO 14

# ===== KHOẢNG THỜI GIAN GỬI DỮ LIỆU =====
SEND_INTERVAL = 16  # Gửi mỗi 16 giây (ThingSpeak yêu cầu ≥ 15 giây)


def connect_wifi():
    """Kết nối WiFi và trả về True nếu thành công"""
    print("=" * 40)
    print("  IoT Lab 03 - Servo + ThingSpeak")
    print("  ESP32 MicroPython")
    print("=" * 40)
    
    wlan = network.WLAN(network.STA_IF)  # Chế độ Station
    wlan.active(True)                     # Bật WiFi
    
    if not wlan.isconnected():
        print(f"Đang kết nối WiFi: {WIFI_SSID}")
        wlan.connect(WIFI_SSID, WIFI_PASS)
        
        # Chờ kết nối (tối đa 20 giây)
        timeout = 0
        while not wlan.isconnected() and timeout < 40:
            time.sleep(0.5)
            print(".", end="")
            timeout += 1
    
    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print(f"\n✓ Kết nối WiFi thành công!")
        print(f"  IP: {ip}")
        return True
    else:
        print("\n✗ Không thể kết nối WiFi!")
        return False


def send_to_thingspeak(angle_left, angle_right):
    """Gửi dữ liệu góc quay 2 servo lên ThingSpeak"""
    try:
        # Tạo URL với tham số
        url = (
            f"{THINGSPEAK_URL}"
            f"?api_key={WRITE_API_KEY}"
            f"&field1={angle_left}"
            f"&field2={angle_right}"
        )
        
        print("--- Gửi dữ liệu lên ThingSpeak ---")
        
        # Gửi HTTP GET request
        response = urequests.get(url)
        
        if response.status_code == 200:
            entry_id = response.text
            print(f"  ✓ Thành công! Entry #{entry_id}")
        else:
            print(f"  ✗ Lỗi HTTP: {response.status_code}")
        
        response.close()  # Đóng kết nối để giải phóng bộ nhớ
        
    except Exception as e:
        print(f"  ✗ Lỗi gửi dữ liệu: {e}")


def main():
    """Hàm chính - Điều khiển servo và gửi dữ liệu"""
    
    # --- Kết nối WiFi ---
    wifi_ok = connect_wifi()
    
    # --- Khởi tạo 2 Servo ---
    servo_left = Servo(SERVO_LEFT_PIN)
    servo_right = Servo(SERVO_RIGHT_PIN)
    print(f"✓ Servo trái khởi tạo trên GPIO {SERVO_LEFT_PIN}")
    print(f"✓ Servo phải khởi tạo trên GPIO {SERVO_RIGHT_PIN}")
    print("=" * 40)
    print("Bắt đầu điều khiển servo...\n")
    
    # --- Biến điều khiển ---
    angle = 0           # Góc hiện tại (bắt đầu từ 0°)
    step = 5             # Mỗi bước tăng/giảm 5°
    going_up = True      # Đang tăng góc?
    last_send = time.time()  # Thời điểm gửi dữ liệu cuối
    
    # --- Vòng lặp chính ---
    while True:
        # == Cập nhật góc quay ==
        if going_up:
            angle += step
            if angle >= 180:
                angle = 180
                going_up = False    # Đổi chiều: bắt đầu giảm
        else:
            angle -= step
            if angle <= 0:
                angle = 0
                going_up = True     # Đổi chiều: bắt đầu tăng
        
        # == Tính góc cho 2 servo ==
        angle_left = angle           # Servo trái: quay theo góc
        angle_right = 180 - angle    # Servo phải: quay ngược chiều
        
        # == Ghi góc vào servo ==
        servo_left.write(angle_left)
        servo_right.write(angle_right)
        
        # == In ra console ==
        print(f"Servo trái: {angle_left:3d}° | Servo phải: {angle_right:3d}°")
        
        # == Gửi dữ liệu lên ThingSpeak (mỗi 16 giây) ==
        now = time.time()
        if wifi_ok and (now - last_send) >= SEND_INTERVAL:
            last_send = now
            send_to_thingspeak(angle_left, angle_right)
            print()
        
        # == Chờ 200ms trước bước tiếp theo ==
        time.sleep(0.2)


# Chạy chương trình
main()