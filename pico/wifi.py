import wifi
import socketpool
import time
import os

class PicoWifi:
    def __init__(self):
        # 从settings.toml读取配置
        self.ssid = os.getenv('CIRCUITPY_WIFI_SSID', 'your_wifi_ssid')
        self.password = os.getenv('CIRCUITPY_WIFI_PASSWORD', 'your_password')
        self.wifi = wifi
        self.socketpool = None
        
    def connect(self):
        """连接到WIFI"""
        try:
            print(f"Connecting to WiFi: {self.ssid}")
            # 先断开现有连接
            try:
                self.wifi.radio.stop_station()
                time.sleep(1)
            except:
                pass
                
            # 连接WiFi
            self.wifi.radio.connect(self.ssid, self.password)
            print("Connected to WiFi")
            
            # 初始化socketpool
            print("Initializing socketpool...")
            self.socketpool = socketpool.SocketPool(self.wifi.radio)
            print("Socketpool initialized")
            
            return True
            
        except Exception as e:
            print(f"Failed to connect to WiFi: {str(e)}")
            self.socketpool = None
            return False
    
    def get_wifi_info(self):
        """获取WIFI连接信息"""
        if self.wifi.radio.connected:
            return str(self.wifi.radio.ipv4_address)
        return "Not connected"
    
    def is_connected(self):
        """检查WIFI连接状态"""
        return self.wifi.radio.connected
