import time
import json
import terminalio
import displayio
from adafruit_display_text.label import Label
from adafruit_display_shapes.rect import Rect

# 应用名称
APP_NAME = "Exchange"

class App:
    def __init__(self, pico, hw, colors):
        print("Initializing Exchange Rate App...")  # 调试信息
        self.pico = pico
        self.hw = hw
        self.display = pico.display
        self.colors = colors
        self.wifi = pico.wifi
        self.request = pico.request
        
        # 创建显示组
        self.main_group = displayio.Group()
        
        # 创建背景
        background = Rect(0, 0, self.display.width, self.display.height, fill=0x000000)
        self.main_group.append(background)
        
        # 创建标题
        self.title = Label(
            terminalio.FONT,
            text="USD to CNY",
            color=colors['text'],
            x=self.display.width // 2 - 30,
            y=20
        )
        self.main_group.append(self.title)
        
        # 创建汇率显示
        self.rate_label = Label(
            terminalio.FONT,
            text="Loading...",
            color=colors['text'],
            x=20,
            y=self.display.height // 2
        )
        self.main_group.append(self.rate_label)
        
        # 创建更新时间显示
        self.time_label = Label(
            terminalio.FONT,
            text="",
            color=colors['hint'],
            x=20,
            y=self.display.height - 20
        )
        self.main_group.append(self.time_label)
        
        # 创建提示
        self.hint = Label(
            terminalio.FONT,
            text="B:Back  A:Refresh",
            color=colors['hint'],
            x=20,
            y=self.display.height - 40
        )
        self.main_group.append(self.hint)
        
        # 上次更新时间
        self.last_update = 0
        print("Exchange Rate App initialized")  # 调试信息
        
    def get_exchange_rate(self):
        """获取汇率数据"""
        try:
            print("Getting exchange rate...")
            
            # 检查WiFi和request是否可用
            if self.wifi is None or self.request is None:
                print("Network components not initialized, attempting to reinitialize...")
                from pico.wifi import PicoWifi
                from pico.request import PicoRequest
                
                # 重新初始化WiFi
                self.wifi = PicoWifi()
                if not self.wifi.is_connected():
                    print("WiFi not connected, connecting...")
                    if not self.wifi.connect():
                        raise Exception("Failed to connect to WiFi")
                
                if not self.wifi.socketpool:
                    print("Socketpool not initialized, reconnecting WiFi...")
                    if not self.wifi.connect():
                        raise Exception("Failed to initialize socketpool")
                
                # 重新初始化request
                print("Reinitializing request client...")
                self.request = PicoRequest(self.wifi.socketpool)
                
            # 确保WiFi已连接
            if not self.wifi.is_connected():
                print("WiFi not connected, connecting...")
                if not self.wifi.connect():
                    raise Exception("Failed to connect to WiFi")
                
            # 使用API获取汇率
            url = "http://open.er-api.com/v6/latest/USD"
            print(f"Fetching data from {url}")
            try:
                response = self.request.get(url)
                print("Response received")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        rate = data['rates']['CNY']
                        print(f"Got rate: {rate}")
                        self.rate_label.text = f"1 USD = {rate:.4f} CNY"
                        current_time = time.localtime()
                        self.time_label.text = f"Updated: {current_time.tm_hour:02d}:{current_time.tm_min:02d}"
                        self.last_update = time.monotonic()
                    except Exception as e:
                        print(f"Error parsing response: {str(e)}")
                        raise Exception(f"Failed to parse response: {str(e)}")
                else:
                    print(f"API request failed with status {response.status_code}")
                    self.rate_label.text = f"Failed: {response.status_code}"
                    
            except Exception as e:
                print(f"Request failed: {str(e)}")
                raise
                
        except Exception as e:
            print(f"Error getting exchange rate: {str(e)}")
            self.rate_label.text = f"Error: {str(e)}"
            # 出错时重置网络组件
            self.request = None
            self.wifi = None
            
    def play(self):
        """运行应用"""
        print("Starting Exchange Rate App...")  # 调试信息
        try:
            # 设置显示
            self.display.root_group = self.main_group
            print("Display group set")  # 调试信息
            
            # 初始获取汇率
            self.get_exchange_rate()
            
            while True:
                try:
                    # 处理按键
                    if self.hw.get_button_state('b'):  # 返回
                        print("Back button pressed")  # 调试信息
                        return True
                        
                    elif self.hw.get_button_state('a'):  # 刷新
                        print("Refresh button pressed")  # 调试信息
                        self.rate_label.text = "Updating..."
                        self.get_exchange_rate()
                        time.sleep(0.2)
                        
                    # 每5分钟自动更新一次
                    if time.monotonic() - self.last_update >= 300:
                        print("Auto updating...")  # 调试信息
                        self.get_exchange_rate()
                        
                except Exception as e:
                    print(f"Error in button handling: {str(e)}")
                    
                time.sleep(0.1)  # 降低循环频率
                
        except Exception as e:
            print(f"Fatal error in Exchange Rate App: {str(e)}")
            return True 