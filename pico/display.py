import board
import os
import busio
import terminalio
import digitalio
import displayio
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font
from adafruit_st7789 import ST7789
import time

class PicoDisplay:
    # 显示屏配置
    DISPLAY_CONFIG = {
        'width': 135,
        'height': 240,
        'rotation': 270,
        'rowstart': 40,
        'colstart': 53,
        'pins': {
            'dc': board.GP8,
            'cs': board.GP9,
            'clk': board.GP10,
            'mosi': board.GP11,
            'rst': board.GP12,
            'backlight': board.GP13
        }
    }

    def __init__(self, tft_rotation=None):
        """初始化显示屏"""
        print("Initializing PicoDisplay...")
        self.rotation = tft_rotation if tft_rotation is not None else self.DISPLAY_CONFIG['rotation']
        self._init_display()
        self.bgcolor_group = self.get_bgcolor_group()
        self.text_group = None
        self._cache = {}
        print("Display initialized successfully")

    def _init_display(self):
        """初始化显示屏硬件"""
        try:
            # 释放之前的显示和重置SPI状态
            displayio.release_displays()
            
            # 重置所有相关引脚
            for pin_name, pin in self.DISPLAY_CONFIG['pins'].items():
                try:
                    io = digitalio.DigitalInOut(pin)
                    io.deinit()
                except Exception as e:
                    print(f"Warning: Could not reset pin {pin_name}: {e}")

            # 初始化SPI
            spi = None
            try:
                # 使用默认配置初始化SPI
                spi = busio.SPI(
                    self.DISPLAY_CONFIG['pins']['clk'],
                    self.DISPLAY_CONFIG['pins']['mosi']
                )
            except Exception as e:
                print(f"Error initializing SPI: {e}")
                if spi:
                    spi.deinit()
                raise

            # 等待一小段时间确保SPI稳定
            time.sleep(0.1)

            # 初始化显示总线
            display_bus = None
            try:
                display_bus = displayio.FourWire(
                    spi,
                    command=self.DISPLAY_CONFIG['pins']['dc'],
                    chip_select=self.DISPLAY_CONFIG['pins']['cs'],
                    reset=self.DISPLAY_CONFIG['pins']['rst']
                )
            except Exception as e:
                print(f"Error initializing display bus: {e}")
                if display_bus:
                    display_bus.deinit()
                if spi:
                    spi.deinit()
                raise

            # 根据旋转调整宽高
            if self.rotation in [90, 270]:
                width = self.DISPLAY_CONFIG['height']
                height = self.DISPLAY_CONFIG['width']
            else:
                width = self.DISPLAY_CONFIG['width']
                height = self.DISPLAY_CONFIG['height']

            # 初始化ST7789显示屏
            try:
                self.display = ST7789(
                    display_bus,
                    rotation=self.rotation,
                    width=width,
                    height=height,
                    rowstart=self.DISPLAY_CONFIG['rowstart'],
                    colstart=self.DISPLAY_CONFIG['colstart'],
                    backlight_pin=self.DISPLAY_CONFIG['pins']['backlight']
                )
            except Exception as e:
                print(f"Error initializing ST7789: {e}")
                if display_bus:
                    display_bus.deinit()
                if spi:
                    spi.deinit()
                raise

            # 初始化显示属性
            self.display_width = width
            self.display_height = height
            self.splash = displayio.Group()
            self.display.root_group = self.splash

        except Exception as e:
            print(f"Error initializing display: {e}")
            raise

    def get_bgcolor_group(self, color=0xFFFFFF):
        """创建背景色组"""
        try:
            color_bitmap = displayio.Bitmap(self.display_width, self.display_height, 1)
            color_palette = displayio.Palette(1)
            color_palette[0] = color
            bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
            bg_group = displayio.Group()
            bg_group.append(bg_sprite)
            return bg_group
        except Exception as e:
            print(f"Error creating background group: {e}")
            raise

    def draw_text(self, text, color=0x000000, x=0, y=0, scale=1, font=None, center=True):
        """绘制文本，支持居中显示"""
        try:
            if font is None:
                font = terminalio.FONT

            # 创建文本区域
            text_area = label.Label(
                font,
                text=text,
                color=color,
                scale=scale
            )
            
            # 如果需要居中显示，计算居中位置
            if center:
                # 获取文本尺寸
                text_width = text_area.bounding_box[2] * scale
                text_height = text_area.bounding_box[3] * scale
                
                # 计算居中位置
                if x == 0:  # 如果x为0，水平居中
                    x = (self.display_width - text_width) // 2
                if y == 0:  # 如果y为0，垂直居中
                    y = (self.display_height - text_height) // 2
            
            # 设置位置
            text_area.x = x
            text_area.y = y
            
            # 添加到显示组
            self.splash.append(text_area)
            return text_area
        except Exception as e:
            print(f"Error drawing text: {e}")
            return None

    def draw_bitmap(self, img_path, x=0, y=0, center=True):
        """绘制位图，支持居中显示"""
        try:
            print(f"Drawing bitmap: {img_path}")
            with open(img_path, "rb") as f:
                bitmap = displayio.OnDiskBitmap(f)
                
                # 如果需要居中显示，计算居中位置
                if center:
                    if x == 0:  # 如果x为0，水平居中
                        x = (self.display_width - bitmap.width) // 2
                    if y == 0:  # 如果y为0，垂直居中
                        y = (self.display_height - bitmap.height) // 2
                
                tile_grid = displayio.TileGrid(
                    bitmap,
                    pixel_shader=bitmap.pixel_shader,
                    x=x,
                    y=y
                )
                self.splash.append(tile_grid)
                return tile_grid
        except Exception as e:
            print(f"Error drawing bitmap {img_path}: {e}")
            return None

    def draw_multiline_text(self, text, color=0x000000, x=0, y=0, scale=1, font=None, line_spacing=1.2):
        """绘制多行文本，支持自动换行"""
        try:
            if font is None:
                font = terminalio.FONT
            
            # 分割文本行
            lines = text.split('\n')
            
            # 计算行高
            line_height = int(font.get_bounding_box()[1] * scale * line_spacing)
            
            # 绘制每一行
            current_y = y
            for line in lines:
                if line.strip():  # 跳过空行
                    self.draw_text(line, color, x, current_y, scale, font)
                current_y += line_height
                
        except Exception as e:
            print(f"Error drawing multiline text: {e}")

    def draw_centered_text(self, text, color=0x000000, y_offset=0, scale=1, font=None):
        """在屏幕中央绘制文本"""
        try:
            if font is None:
                font = terminalio.FONT
            
            # 创建文本区域以获取尺寸
            text_area = label.Label(
                font,
                text=text,
                color=color,
                scale=scale
            )
            
            # 计算居中位置
            x = (self.display_width - text_area.bounding_box[2] * scale) // 2
            y = (self.display_height - text_area.bounding_box[3] * scale) // 2 + y_offset
            
            # 设置位置并显示
            text_area.x = x
            text_area.y = y
            self.splash.append(text_area)
            return text_area
            
        except Exception as e:
            print(f"Error drawing centered text: {e}")
            return None

    def clear_display(self):
        """清除显示内容"""
        try:
            while len(self.splash) > 0:
                self.splash.pop()
            self.bgcolor_group = self.get_bgcolor_group()
            self.splash.append(self.bgcolor_group)
        except Exception as e:
            print(f"Error clearing display: {e}")

    def draw_background(self, color):
        """绘制背景"""
        try:
            color_bitmap = displayio.Bitmap(self.display_width, self.display_height, 1)
            color_palette = displayio.Palette(1)
            color_palette[0] = color
            bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
            self.splash.append(bg_sprite)
        except Exception as e:
            print(f"Error drawing background: {e}")

    def get_center_position(self, width, height):
        """获取居中位置"""
        return (
            (self.display_width - width) // 2,
            (self.display_height - height) // 2
        )

    def cleanup(self):
        """清理资源"""
        try:
            self.clear_display()
            displayio.release_displays()
        except Exception as e:
            print(f"Error during cleanup: {e}")

    def __del__(self):
        """析构函数，确保资源被释放"""
        try:
            self.cleanup()
        except Exception as e:
            print(f"Error in __del__: {e}")
