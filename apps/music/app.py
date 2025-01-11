import displayio
import terminalio
from adafruit_display_text import label
import os
import time
from pico.buzzer import PicoBuzzer

# 应用名称，将显示在菜单中
APP_NAME = "Music"

class App:
    def __init__(self, display, hw, colors):
        self.display = display
        self.hw = hw
        self.colors = colors
        
        # 菜单显示参数
        self.center_y = self.display.display_height // 2
        self.y_positions = [-30, 0, 30]  # 上中下三个位置的Y偏移
        
        # 初始化蜂鸣器
        self.buzzer = PicoBuzzer()
        
        # 音乐列表
        self.music_files = self.get_music_files()
        self.current_index = 0
        
        # 初始化显示
        self.init_display()
        
    def get_music_files(self):
        """获取音乐文件列表"""
        try:
            music_dir = "/apps/music/resources"
            print(f"Checking music directory: {music_dir}")
            
            # 检查目录是否存在
            try:
                os.stat(music_dir)
            except OSError as e:
                print(f"Directory does not exist: {e}")
                try:
                    print("Creating directory...")
                    os.makedirs(music_dir)
                except Exception as e:
                    print(f"Failed to create directory: {e}")
                return ["No Music Files"]
            
            # 列出文件
            try:
                files = os.listdir(music_dir)
                print(f"Files in directory: {files}")
            except Exception as e:
                print(f"Error listing directory: {e}")
                return ["No Music Files"]
            
            # 过滤txt文件
            music_files = [f for f in files if f.endswith('.txt')]
            print(f"Found music files: {music_files}")
            
            if not music_files:
                print("No .txt files found")
                return ["No Music Files"]
            
            return sorted(music_files)
            
        except Exception as e:
            print(f"Error in get_music_files: {e}")
            return ["No Music Files"]
            
    def get_music_name(self, filename):
        """从文件名获取音乐名称"""
        if filename == "No Music Files":
            return filename
            
        # 移除.txt后缀并将下划线替换为空格
        name = filename.replace('.txt', '').replace('_', ' ')
        
        # 手动将每个单词首字母大写
        words = name.split(' ')
        capitalized_words = []
        for word in words:
            if word:  # 确保单词不为空
                capitalized_words.append(word[0].upper() + word[1:].lower())
        return ' '.join(capitalized_words)
        
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
        
    def add_hints(self):
        """添加固定的提示文本"""
        hints = [
            ("A:Play", 5),
            ("B:Back", self.display.display_width - 50)
        ]
        
        for text, x in hints:
            self.main_group.append(
                self.create_text_label(
                    text,
                    self.colors['hint'],
                    x,
                    self.display.display_height - 15
                )
            )
            
    def draw_menu_items(self):
        """绘制菜单项"""
        # 移除旧的菜单项（保留背景和提示）
        while len(self.main_group) > 3:
            self.main_group.pop()
            
        total_files = len(self.music_files)
        
        # 绘制三个位置的菜单项（上中下）
        for i, y_offset in enumerate(self.y_positions):
            # 计算要显示的文件索引
            file_index = (self.current_index - 1 + i) % total_files
            if file_index < 0:
                file_index += total_files
                
            # 计算Y坐标
            y = self.center_y + y_offset
            
            # 设置颜色
            color = self.colors['selected'] if i == 1 else self.colors['text']
            
            # 绘制选中项指示器
            if i == 1:  # 中间项
                self.main_group.append(
                    self.create_text_label(">", color, 35, y)
                )
                
            # 绘制文件名
            filename = self.music_files[file_index]
            text = self.get_music_name(filename)
            if len(text) > 20:  # 截断过长的文件名
                text = text[:17] + "..."
            self.main_group.append(
                self.create_text_label(text, color, 50, y)
            )
            
    def show_playing_screen(self, music_name):
        """显示播放界面"""
        # 清除显示
        self.main_group = displayio.Group()
        
        # 绘制背景
        color_bitmap = displayio.Bitmap(self.display.display_width, self.display.display_height, 1)
        color_palette = displayio.Palette(1)
        color_palette[0] = self.colors['background']
        bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
        self.main_group.append(bg_sprite)
        
        # 显示正在播放的信息（使用hint颜色，更柔和）
        now_playing = self.create_text_label(
            "Now Playing",
            self.colors['hint'],
            self.display.display_width // 2,
            self.center_y - 30,  # 向上移动一些
            True
        )
        self.main_group.append(now_playing)
        
        # 显示音乐名称（使用selected颜色，更突出）
        name_label = self.create_text_label(
            music_name,
            self.colors['selected'],
            self.display.display_width // 2,
            self.center_y,  # 居中显示
            True
        )
        self.main_group.append(name_label)
        
        # 显示按键提示（移到底部）
        hint_label = self.create_text_label(
            "Press B to stop",
            self.colors['hint'],
            self.display.display_width // 2,
            self.display.display_height - 20,
            True
        )
        self.main_group.append(hint_label)
        
        # 更新显示
        self.display.display.root_group = self.main_group
            
    def play_music_loop(self, filename):
        """循环播放音乐直到按B键停止"""
        try:
            # 创建中断检查函数
            def check_interrupt():
                """检查是否需要中断播放"""
                return self.hw.get_button_state('b')
            
            music_path = f"/apps/music/resources/{filename}"
            print(f"Playing music: {music_path}")
            
            # 循环播放直到按B键停止
            while not check_interrupt():
                self.buzzer.play_from_file(music_path, check_interrupt)
                if check_interrupt():  # 再次检查，避免开始新的循环
                    break
                    
        except Exception as e:
            print(f"Error in music loop: {e}")
            print(f"Details: {str(e)}")  # 添加更多错误信息
            
    def play(self):
        """播放音乐"""
        try:
            self.init_display()
            self.draw_menu_items()
            
            while True:
                if self.hw.get_button_state('up'):
                    self.current_index = (self.current_index - 1) % len(self.music_files)
                    self.draw_menu_items()
                    time.sleep(0.2)
                    
                elif self.hw.get_button_state('down'):
                    self.current_index = (self.current_index + 1) % len(self.music_files)
                    self.draw_menu_items()
                    time.sleep(0.2)
                    
                elif self.hw.get_button_state('a'):
                    if self.music_files[self.current_index] == "No Music Files":
                        continue
                        
                    # 显示播放界面
                    music_name = self.get_music_name(self.music_files[self.current_index])
                    self.show_playing_screen(music_name)
                    
                    # 播放音乐
                    self.play_music_loop(self.music_files[self.current_index])
                    
                    # 返回菜单
                    self.init_display()
                    self.draw_menu_items()
                    time.sleep(0.2)  # 防止按键重复触发
                    
                elif self.hw.get_button_state('b'):
                    return True
                    
                time.sleep(0.05)  # 短暂延时，减少CPU占用
                
        except Exception as e:
            print(f"Error in play: {e}")
            return True 