import adafruit_requests
import gc

class PicoRequest:
    def __init__(self, socketpool=None):
        if socketpool is None:
            print("Error: socketpool is None")
            raise ValueError("socketpool cannot be None")
        try:
            print("Initializing request session...")
            self.r = adafruit_requests.Session(socketpool)
            print("Request session initialized")
        except Exception as e:
            print(f"Error initializing request session: {str(e)}")
            raise
        
    def get(self, url):
        return self.request("GET", url)
        
    def post(self, url):
        return self.request("POST", url)

    def request(self, method, url):
        try:
            # 在请求前执行垃圾回收
            gc.collect()
            print(f"Making {method} request to {url}")
            
            if method == "GET":
                print("Creating GET request...")
                response = self.r.get(url)
                print(f"Response received, status code: {response.status_code}")
            elif method == "POST":
                print("Creating POST request...")
                response = self.r.post(url)
                print(f"Response received, status code: {response.status_code}")
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            return response
            
        except Exception as e:
            print(f"Request error: {str(e)}")
            if hasattr(e, '__class__'):
                print(f"Error type: {e.__class__.__name__}")
            raise
"""
example:
from pico_wifi import PicoWifi
from pico_request import PicoRequest

#初始化wifi
wifi = PicoWifi()
ip = wifi.get_wifi_info()
#初始化请求
request = PicoRequest(wifi.radio)
#各种初始化的请求不应该放在while循环中，否则会导致内存泄漏
while True:
        response = request.get("https://yjiang.cn/other/notice.html")
        print(response)
"""
