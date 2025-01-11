import time
import displayio
import gc
import os
from pico.display import PicoDisplay
from pico.hardware import PicoHardware

# 应用名称，将显示在菜单中
APP_NAME = "CXK"

class App:
    def __init__(self, display: PicoDisplay, hardware: PicoHardware, colors=None):
        self.pico = display
        self.hw = hardware
        self.colors = colors if colors else {
            'background': 0x000000,    # 黑色背景
            'normal': 0x808080,        # 灰色未选中
            'selected': 0x00FF00,      # 绿色选中
            'hint': 0x404040,          # 深灰色提示
            'score': 0xFFFFFF,         # 白色分数
            'error': 0xFF0000          # 红色错误
        }
        
    def get_cxk_images(self):
        """获取CXK图片序列"""
        try:
            files = os.listdir("/apps/cxk/resources")
            # 筛选CXK前缀的bmp文件
            images = [f for f in files if f.startswith('cxk') and f.endswith('.bmp')]
            # 按字母顺序排序
            images.sort()
            return [f"/apps/cxk/resources/{img}" for img in images]
        except Exception as e:
            print(f"Error listing images: {e}")
            return []
            
    def preload_image(self, img_path):
        """预加载图片"""
        try:
            bitmap = displayio.OnDiskBitmap(open(img_path, "rb"))
            
            # 计算缩放后的尺寸，使图片填满屏幕但保持比例
            scale_w = self.pico.display_width / bitmap.width
            scale_h = self.pico.display_height / bitmap.height
            scale = min(scale_w, scale_h)  # 使用较小的缩放比例以适应屏幕
            
            # 计算居中位置
            x = (self.pico.display_width - bitmap.width) // 2
            y = (self.pico.display_height - bitmap.height) // 2
            
            tile_grid = displayio.TileGrid(
                bitmap,
                pixel_shader=bitmap.pixel_shader,
                x=x,
                y=y
            )
            return tile_grid
        except Exception as e:
            print(f"Error loading image {img_path}: {e}")
            return None
            
    def create_background(self):
        """创建白色背景"""
        color_bitmap = displayio.Bitmap(self.pico.display_width, self.pico.display_height, 1)
        color_palette = displayio.Palette(1)
        color_palette[0] = 0xFFFFFF
        return displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
            
    def play(self):
        """播放CXK动画"""
        image_list = self.get_cxk_images()
        
        if not image_list:
            try:
                print("No images found")
                # 清除当前显示
                self.pico.clear_display()
                
                # 显示错误信息
                self.pico.draw_text(
                    "No images found!",
                    color=0xFF0000,  # 红色
                    x=0,
                    y=self.pico.display_height // 2,
                    scale=2,
                    center=True
                )
                
                time.sleep(2)
                return True  # 返回True表示需要刷新菜单
            except Exception as e:
                print(f"Error displaying no images message: {e}")
                return True

        try:
            # 预加载所有图片
            print("Preloading images...")
            image_grids = []
            for img_path in image_list:
                grid = self.preload_image(img_path)
                if grid:
                    image_grids.append(grid)
            
            print(f"Successfully loaded {len(image_grids)} images")
            
            # 创建两个显示组用于双缓冲
            group1 = displayio.Group()
            group2 = displayio.Group()
            
            # 为每个组添加独立的白色背景
            group1.append(self.create_background())
            group2.append(self.create_background())
            
            print("Starting animation loop...")
            
            # 循环显示图片
            current_group = group1
            frame_delay = 0.05  # 20fps
            
            # 播放动画直到按键被按下
            while True:
                for grid in image_grids:
                    try:
                        # 检查按键状态
                        if self.hw.get_button_state('b'):  # 使用B键退出
                            print("B button pressed, returning to menu...")
                            return True  # 返回True表示需要刷新菜单
                            
                        # 切换显示组
                        next_group = group2 if current_group == group1 else group1
                        
                        # 清除旧内容
                        while len(next_group) > 1:  # 保留背景
                            next_group.pop()
                        
                        # 添加新图片
                        next_group.append(grid)
                        
                        # 切换显示
                        self.pico.display.root_group = next_group
                        current_group = next_group
                        
                        # 短暂延时
                        time.sleep(frame_delay)
                        
                        # 垃圾回收
                        gc.collect()
                        
                    except Exception as e:
                        print(f"Error in animation loop: {e}")
                        time.sleep(0.1)
        except Exception as e:
            print(f"Error in main process: {e}")
            time.sleep(1)
        return True  # 返回True表示需要刷新菜单 