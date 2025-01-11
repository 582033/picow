import microcontroller
import board
import digitalio
import time

class PicoHardware:
    # 按键定义
    BUTTON_PINS = {
        'up': board.GP2,
        'down': board.GP18,
        'ctl': board.GP3,
        'left': board.GP16,
        'right': board.GP20,
        'a': board.GP15,
        'b': board.GP17
    }

    def __init__(self):
        """初始化硬件控制"""
        print("Initializing PicoHardware...")
        self.buttons = {}
        self._button_states = {}  # 记录按键状态
        self._last_press_times = {}  # 每个按键独立的防抖时间
        self._init_buttons()
        self._debounce_delay = 0.02  # 降低防抖延时到20ms

    def _init_buttons(self):
        """初始化所有按键"""
        try:
            for name, pin in self.BUTTON_PINS.items():
                button = digitalio.DigitalInOut(pin)
                button.direction = digitalio.Direction.INPUT
                button.pull = digitalio.Pull.UP
                self.buttons[name] = button
                self._button_states[name] = True  # 初始状态为未按下
                self._last_press_times[name] = 0
            print("Buttons initialized successfully")
        except Exception as e:
            print(f"Error initializing buttons: {e}")
            raise

    def get_button_state(self, button_name):
        """获取按键状态（带防抖）"""
        if button_name not in self.buttons:
            return False

        current_time = time.monotonic()
        button = self.buttons[button_name]
        
        # 读取当前按键状态
        current_state = not button.value

        # 如果状态没有改变，直接返回
        if current_state == self._button_states[button_name]:
            return current_state

        # 状态改变时进行防抖处理
        if current_time - self._last_press_times[button_name] >= self._debounce_delay:
            self._button_states[button_name] = current_state
            self._last_press_times[button_name] = current_time
            return current_state

        return self._button_states[button_name]

    def is_button_pressed(self, button_name):
        """检查按键是否被按下"""
        return self.get_button_state(button_name)

    def any_button_pressed(self):
        """检查是否有任何按键被按下"""
        return any(self.get_button_state(name) for name in self.buttons)

    def wait_for_button(self, button_name, timeout=None):
        """等待指定按键被按下"""
        if button_name not in self.buttons:
            return False
            
        start_time = time.monotonic()
        while True:
            if timeout and (time.monotonic() - start_time > timeout):
                return False
            if self.get_button_state(button_name):
                return True
            time.sleep(0.001)  # 1ms延时，减少CPU占用

    def cleanup(self):
        """清理资源"""
        for button in self.buttons.values():
            button.deinit()

    def get_cpu_temperature(self):
        """获取CPU温度"""
        try:
            temp = microcontroller.cpu.temperature
            return f"{temp:.1f} °C"
        except Exception as e:
            print(f"Error reading CPU temperature: {e}")
            return "Error"

    def get_cpu_frequency(self):
        """获取CPU频率"""
        try:
            freq = microcontroller.cpu.frequency
            return f"{freq // 1_000_000} MHz"
        except Exception as e:
            print(f"Error reading CPU frequency: {e}")
            return "Error"

    def set_cpu_frequency(self, mhz):
        """设置CPU频率"""
        try:
            if not (100 <= mhz <= 200):
                raise ValueError("Frequency must be between 100 and 200 MHz")
            microcontroller.cpu.frequency = mhz * 1_000_000
            return True
        except Exception as e:
            print(f"Error setting CPU frequency: {e}")
            return False

    def get_system_info(self):
        """获取系统信息"""
        return {
            'temperature': self.get_cpu_temperature(),
            'frequency': self.get_cpu_frequency(),
            'buttons': list(self.buttons.keys())
        }

    def __del__(self):
        """析构函数，确保资源被正确释放"""
        self.cleanup()
