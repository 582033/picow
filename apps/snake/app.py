import time
import random
import displayio
import terminalio
from adafruit_display_text import label
from adafruit_display_shapes.rect import Rect

# 应用名称，将显示在菜单中
APP_NAME = "Snake"

class App:
    def __init__(self, pico, hw, colors):
        self.pico = pico
        self.hw = hw
        self.display = pico.display
        self.GRID_SIZE = 10  # 每个网格的大小
        self.WIDTH = self.display.width // self.GRID_SIZE
        self.HEIGHT = self.display.height // self.GRID_SIZE
        self.snake = [(self.WIDTH//4, self.HEIGHT//2)]  # 蛇的初始位置
        self.direction = (1, 0)  # 初始方向向右
        self.food = None
        self.score = 0
        self.game_over = False
        self.colors = colors
        
        # 创建背景
        self.bg_bitmap = displayio.Bitmap(self.display.width, self.display.height, 1)
        self.bg_palette = displayio.Palette(1)
        self.bg_palette[0] = self.colors['background']
        self.bg_sprite = displayio.TileGrid(self.bg_bitmap, pixel_shader=self.bg_palette)
        
        # 创建显示组
        self.main_group = displayio.Group()
        self.main_group.append(self.bg_sprite)
        self.game_group = displayio.Group()
        self.main_group.append(self.game_group)
        
        # 创建分数标签
        self.score_label = label.Label(
            terminalio.FONT,
            text="Score: 0",
            color=0xFFFFFF,
            x=5,
            y=5
        )
        self.main_group.append(self.score_label)
        
    def generate_food(self):
        while True:
            x = random.randint(0, self.WIDTH-1)
            y = random.randint(0, self.HEIGHT-1)
            if (x, y) not in self.snake:
                self.food = (x, y)
                break
    
    def draw_game(self):
        # 清除之前的游戏元素
        while len(self.game_group) > 0:
            self.game_group.pop()
        
        # 绘制蛇
        for x, y in self.snake:
            rect = Rect(
                x * self.GRID_SIZE, 
                y * self.GRID_SIZE, 
                self.GRID_SIZE-1, 
                self.GRID_SIZE-1, 
                fill=0xFFFFFF
            )
            self.game_group.append(rect)
        
        # 绘制食物
        if self.food:
            food_rect = Rect(
                self.food[0] * self.GRID_SIZE, 
                self.food[1] * self.GRID_SIZE, 
                self.GRID_SIZE-1, 
                self.GRID_SIZE-1, 
                fill=0xFF0000
            )
            self.game_group.append(food_rect)
        
        # 更新分数
        self.score_label.text = f"Score: {self.score}"
        
        # 更新显示
        self.display.root_group = self.main_group
    
    def update(self):
        # 获取新的蛇头位置
        new_head = (
            (self.snake[0][0] + self.direction[0]) % self.WIDTH,
            (self.snake[0][1] + self.direction[1]) % self.HEIGHT
        )
        
        # 检查是否撞到自己
        if new_head in self.snake[1:]:
            self.game_over = True
            return
        
        # 移动蛇
        self.snake.insert(0, new_head)
        
        # 检查是否吃到食物
        if self.food and new_head == self.food:
            self.score += 10
            self.generate_food()
        else:
            self.snake.pop()
    
    def show_start_screen(self):
        """显示开始界面"""
        start_group = displayio.Group()
        
        # 绘制背景
        bg = displayio.Bitmap(self.display.width, self.display.height, 1)
        palette = displayio.Palette(1)
        palette[0] = self.colors['background']
        bg_sprite = displayio.TileGrid(bg, pixel_shader=palette)
        start_group.append(bg_sprite)
        
        # 显示标题
        title = label.Label(
            terminalio.FONT,
            text="Snake Game",
            color=self.colors['selected'],
            anchor_point=(0.5, 0.5),
            anchored_position=(self.display.width // 2, self.display.height // 2 - 20)
        )
        start_group.append(title)
        
        # 显示提示
        hint = label.Label(
            terminalio.FONT,
            text="Press A to Start",
            color=self.colors['hint'],
            anchor_point=(0.5, 0.5),
            anchored_position=(self.display.width // 2, self.display.height // 2 + 20)
        )
        start_group.append(hint)
        
        self.display.root_group = start_group
        
    def show_game_over(self):
        """显示游戏结束界面"""
        over_group = displayio.Group()
        
        # 绘制背景
        bg = displayio.Bitmap(self.display.width, self.display.height, 1)
        palette = displayio.Palette(1)
        palette[0] = self.colors['background']
        bg_sprite = displayio.TileGrid(bg, pixel_shader=palette)
        over_group.append(bg_sprite)
        
        # 显示游戏结束
        title = label.Label(
            terminalio.FONT,
            text="Game Over",
            color=self.colors['error'],
            anchor_point=(0.5, 0.5),
            anchored_position=(self.display.width // 2, self.display.height // 2 - 20)
        )
        over_group.append(title)
        
        # 显示分数
        score = label.Label(
            terminalio.FONT,
            text=f"Score: {self.score}",
            color=self.colors['selected'],
            anchor_point=(0.5, 0.5),
            anchored_position=(self.display.width // 2, self.display.height // 2 + 10)
        )
        over_group.append(score)
        
        self.display.root_group = over_group
        time.sleep(2)
        
    def play(self):
        """开始游戏"""
        # 显示开始界面
        self.show_start_screen()
        
        # 等待开始按键
        while True:
            if self.hw.get_button_state('a'):  # A键开始
                break
            elif self.hw.get_button_state('b'):  # B键返回
                return
            time.sleep(0.1)
            
        # 初始化游戏
        self.snake = [(self.WIDTH//4, self.HEIGHT//2)]
        self.direction = (1, 0)
        self.score = 0
        self.game_over = False
        self.generate_food()
        
        last_update = time.monotonic()
        update_interval = 0.2  # 控制游戏速度
        
        # 游戏主循环
        while not self.game_over:
            current_time = time.monotonic()
            
            # 处理按键输入
            if self.hw.get_button_state('up') and self.direction != (0, 1):
                self.direction = (0, -1)
            elif self.hw.get_button_state('down') and self.direction != (0, -1):
                self.direction = (0, 1)
            elif self.hw.get_button_state('left') and self.direction != (1, 0):
                self.direction = (-1, 0)
            elif self.hw.get_button_state('right') and self.direction != (-1, 0):
                self.direction = (1, 0)
            elif self.hw.get_button_state('b'):  # B键退出
                break
            
            # 按固定时间间隔更新游戏状态
            if current_time - last_update >= update_interval:
                self.update()
                self.draw_game()
                last_update = current_time
            
            time.sleep(0.01)  # 小延迟防止CPU占用过高
        
        # 显示游戏结束界面
        if self.game_over:
            self.show_game_over()
            
        return True  # 返回True表示需要刷新菜单 