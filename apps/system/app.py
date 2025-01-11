import displayio
import terminalio
from adafruit_display_text import label
import time
import gc
import microcontroller
import os

# 应用名称
APP_NAME = "System"

class App:
    def __init__(self, display, hw, colors):
        self.display = display
        self.hw = hw
        self.colors = colors
        
        # 显示参数
        self.center_y = self.display.display_height // 2
        
        # 创建标签组
        self.labels = {}
        
        # 初始化显示
        self.init_display()
        
    def init_display(self):
        """初始化显示"""
        self.main_group = displayio.Group()
        
        # 创建背景
        bg_bitmap = displayio.Bitmap(
            self.display.display_width,
            self.display.display_height,
            1
        )
        bg_palette = displayio.Palette(1)
        bg_palette[0] = self.colors['background']
        self.main_group.append(
            displayio.TileGrid(bg_bitmap, pixel_shader=bg_palette)
        )
        
        # 创建所有标签
        self.create_all_labels()
        
        # 添加提示文本
        self.add_hints()
        
        # 设置显示组
        self.display.display.root_group = self.main_group
        
    def create_text_label(self, text, color, x, y, center=False):
        """创建文本标签"""
        text_area = label.Label(
            terminalio.FONT,
            text=text,
            color=color
        )
        if center:
            text_area.anchor_point = (0.5, 0.5)
            text_area.anchored_position = (x, y)
        else:
            text_area.x = x
            text_area.y = y
        return text_area
        
    def create_all_labels(self):
        """创建所有标签"""
        # 标题
        title = self.create_text_label(
            "System Info",
            self.colors['selected'],
            self.display.display_width // 2,
            12,
            True
        )
        self.main_group.append(title)
        
        # CPU信息
        y = 30
        self.main_group.append(self.create_text_label(
            "CPU",
            self.colors['text'],
            10,
            y
        ))
        self.labels['cpu_temp'] = self.create_text_label("", self.colors['text'], 50, y)
        self.labels['cpu_freq'] = self.create_text_label("", self.colors['text'], 120, y)
        self.main_group.append(self.labels['cpu_temp'])
        self.main_group.append(self.labels['cpu_freq'])
        
        # 内存信息
        y = 50
        self.main_group.append(self.create_text_label(
            "MEM",
            self.colors['text'],
            10,
            y
        ))
        # 使用进度条显示内存使用情况
        self.labels['mem_usage'] = self.create_text_label("", self.colors['text'], 50, y)
        self.labels['mem_detail'] = self.create_text_label("", self.colors['text'], 120, y)
        self.main_group.append(self.labels['mem_usage'])
        self.main_group.append(self.labels['mem_detail'])
        
        # 存储信息
        y = 70
        self.main_group.append(self.create_text_label(
            "STO",
            self.colors['text'],
            10,
            y
        ))
        # 使用进度条显示存储使用情况
        self.labels['storage_usage'] = self.create_text_label("", self.colors['text'], 50, y)
        self.labels['storage_detail'] = self.create_text_label("", self.colors['text'], 120, y)
        self.main_group.append(self.labels['storage_usage'])
        self.main_group.append(self.labels['storage_detail'])
            
    def add_hints(self):
        """添加固定的提示文本"""
        hint_label = self.create_text_label(
            "B:Back",
            self.colors['hint'],
            self.display.display_width - 50,
            self.display.display_height - 15
        )
        self.main_group.append(hint_label)
        
    def get_system_info(self):
        """获取系统信息"""
        try:
            # CPU信息
            cpu_temp = microcontroller.cpu.temperature
            cpu_freq = microcontroller.cpu.frequency
            cpu_freq_mhz = cpu_freq/1000000
            
            # 内存信息
            gc.collect()  # 先进行垃圾回收
            mem_free = gc.mem_free()
            mem_alloc = gc.mem_alloc()
            mem_total = mem_free + mem_alloc
            mem_usage = mem_alloc/mem_total
            
            # 磁盘信息
            try:
                fs_stat = os.statvfs('/')
                flash_size = fs_stat[0] * fs_stat[2]  # 总大小
                flash_free = fs_stat[0] * fs_stat[3]  # 可用空间
                flash_used = flash_size - flash_free
                storage_usage = flash_used/flash_size
            except:
                flash_size = 0
                flash_free = 0
                flash_used = 0
                storage_usage = 0
                
            # 生成进度条
            def make_progress_bar(value, length=10):
                filled = int(value * length)
                return '[' + '█' * filled + '.' * (length - filled) + ']'
                
            return {
                'cpu': {
                    'temp': f"{cpu_temp:.1f}°C",
                    'freq': f"{cpu_freq_mhz:.0f}MHz"
                },
                'memory': {
                    'usage': make_progress_bar(mem_usage),
                    'detail': f"{mem_alloc/1024:.0f}K/{mem_total/1024:.0f}K"
                },
                'storage': {
                    'usage': make_progress_bar(storage_usage),
                    'detail': f"{flash_used/1024:.0f}K/{flash_size/1024:.0f}K"
                }
            }
        except Exception as e:
            print(f"Error getting system info: {e}")
            return None
            
    def update_display(self):
        """更新显示"""
        # 获取系统信息
        info = self.get_system_info()
        if not info:
            return
            
        # 更新标签文本
        self.labels['cpu_temp'].text = info['cpu']['temp']
        self.labels['cpu_freq'].text = info['cpu']['freq']
        self.labels['mem_usage'].text = info['memory']['usage']
        self.labels['mem_detail'].text = info['memory']['detail']
        self.labels['storage_usage'].text = info['storage']['usage']
        self.labels['storage_detail'].text = info['storage']['detail']
        
    def play(self):
        """运行应用"""
        try:
            last_update = 0
            # 等待按键释放
            while self.hw.get_button_state('b'):
                time.sleep(0.1)
                
            # 显示初始数据
            self.update_display()
            
            while True:
                # 检查退出
                if self.hw.get_button_state('b'):
                    # 等待按键释放
                    time.sleep(0.2)
                    while self.hw.get_button_state('b'):
                        time.sleep(0.1)
                    return True
                    
                # 每秒更新一次
                current_time = time.monotonic()
                if current_time - last_update >= 1:
                    self.update_display()
                    last_update = current_time
                    
                time.sleep(0.1)  # 减少CPU占用
                
        except Exception as e:
            print(f"Error in system monitor: {e}")
            return True 