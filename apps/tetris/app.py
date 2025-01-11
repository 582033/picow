from pico.display import PicoDisplay
from pico.hardware import PicoHardware
import displayio
import terminalio
from adafruit_display_text import label
from adafruit_display_shapes.rect import Rect
import random
import time

# 应用名称，将显示在菜单中
APP_NAME = "Tetris"

class App:
    def __init__(self, pico, hw, colors):
        self.pico = pico
        self.hw = hw
        self.display = pico.display
        
        # 合并通用颜色和游戏特有颜色
        self.colors = colors.copy()
        self.colors.update({
            'grid': 0x404040,          # 深灰色网格
            'block_i': 0x00FFFF,       # 青色 I 方块
            'block_o': 0xFFFF00,       # 黄色 O 方块
            'block_t': 0xFF00FF,       # 紫色 T 方块
            'block_l': 0xFF8000,       # 橙色 L 方块
            'block_j': 0x0000FF,       # 蓝色 J 方块
            'block_s': 0x00FF00,       # 绿色 S 方块
            'block_z': 0xFF0000        # 红色 Z 方块
        })
        
        # 游戏区域设置 - 适配1.14寸屏幕(135x240)
        self.GRID_SIZE = 8  # 每个方块的大小
        self.BOARD_WIDTH = 10  # 游戏区域宽度
        self.BOARD_HEIGHT = 14  # 游戏区域高度
        self.BOARD_X = (self.display.width - self.BOARD_WIDTH * self.GRID_SIZE) // 2
        self.BOARD_Y = 15  # 顶部边距，为分数留出空间
        
        # 游戏状态
        self.score = 0
        self.level = 1
        self.board = [[None for _ in range(self.BOARD_WIDTH)] for _ in range(self.BOARD_HEIGHT)]
        self.current_piece = None
        self.current_shape = None
        self.rotation_index = 0
        self.piece_x = 0
        self.piece_y = 0
        
        # 定义方块形状和旋转状态
        self.shapes = {
            'I': [[(0,0), (0,1), (0,2), (0,3)],
                  [(0,1), (1,1), (2,1), (3,1)]],
            'O': [[(0,0), (0,1), (1,0), (1,1)]],
            'T': [[(1,0), (0,1), (1,1), (2,1)],
                  [(1,0), (1,1), (2,1), (1,2)],
                  [(0,1), (1,1), (2,1), (1,2)],
                  [(1,0), (0,1), (1,1), (1,2)]],
            'L': [[(0,0), (0,1), (0,2), (1,2)],
                  [(0,1), (1,1), (2,1), (0,0)],
                  [(0,0), (1,0), (1,1), (1,2)],
                  [(2,0), (0,1), (1,1), (2,1)]],
            'J': [[(1,0), (1,1), (1,2), (0,2)],
                  [(0,1), (1,1), (2,1), (2,0)],
                  [(1,0), (0,0), (0,1), (0,2)],
                  [(0,1), (1,1), (2,1), (0,0)]],
            'S': [[(1,0), (2,0), (0,1), (1,1)],
                  [(0,0), (0,1), (1,1), (1,2)]],
            'Z': [[(0,0), (1,0), (1,1), (2,1)],
                  [(1,0), (1,1), (0,1), (0,2)]]
        }
        
        # 创建显示组
        self.main_group = displayio.Group()
        self.game_group = displayio.Group()
        self.main_group.append(self.game_group)
        
        # 创建分数标签
        self.score_label = label.Label(
            terminalio.FONT,
            text="Score: 0",
            color=self.colors['text'],
            x=5,
            y=5
        )
        self.main_group.append(self.score_label)
        
    def play(self):
        """开始游戏"""
        # 初始化游戏
        self.score = 0
        self.level = 1
        self.board = [[None for _ in range(self.BOARD_WIDTH)] for _ in range(self.BOARD_HEIGHT)]
        
        # 生成第一个方块
        self.new_piece()
        self.draw_game()
        
        last_drop = time.monotonic()
        last_move = time.monotonic()
        drop_interval = 0.8  # 初始下落间隔
        
        # 游戏主循环
        while True:
            current_time = time.monotonic()
            
            # 处理按键输入
            if current_time - last_move >= 0.1:  # 按键响应延迟
                if self.hw.get_button_state('left'):
                    if self.can_move(-1, 0):
                        self.piece_x -= 1
                        self.draw_game()
                        last_move = current_time
                        
                elif self.hw.get_button_state('right'):
                    if self.can_move(1, 0):
                        self.piece_x += 1
                        self.draw_game()
                        last_move = current_time
                        
                elif self.hw.get_button_state('down'):
                    if self.can_move(0, 1):
                        self.piece_y += 1
                        self.draw_game()
                        last_move = current_time
                        last_drop = current_time
                        
                elif self.hw.get_button_state('a'):
                    if self.rotate_piece():
                        self.draw_game()
                        last_move = current_time
                        
                elif self.hw.get_button_state('b'):
                    return True
                    
            # 自动下落
            current_drop_interval = drop_interval * (0.5 ** (self.level - 1))  # 随等级加快
            if current_time - last_drop >= current_drop_interval:
                if self.can_move(0, 1):
                    self.piece_y += 1
                else:
                    self.place_piece()
                    self.check_lines()
                    self.new_piece()
                    if not self.can_move(0, 0):  # 游戏结束检查
                        self.show_game_over()
                        return True
                self.draw_game()
                last_drop = current_time
                
            time.sleep(0.01)  # 防止CPU占用过高 
        
    def new_piece(self):
        """生成新的方块"""
        self.current_shape = random.choice(list(self.shapes.keys()))
        self.rotation_index = 0
        self.current_piece = self.shapes[self.current_shape][self.rotation_index]
        self.piece_x = self.BOARD_WIDTH // 2 - 2
        self.piece_y = 0
        
    def rotate_piece(self):
        """旋转当前方块"""
        if not self.current_piece:
            return False
            
        new_rotation = (self.rotation_index + 1) % len(self.shapes[self.current_shape])
        new_piece = self.shapes[self.current_shape][new_rotation]
        
        # 检查旋转后是否有效
        for x, y in new_piece:
            new_x = self.piece_x + x
            new_y = self.piece_y + y
            if (new_x < 0 or new_x >= self.BOARD_WIDTH or 
                new_y >= self.BOARD_HEIGHT or
                (new_y >= 0 and self.board[new_y][new_x])):
                return False
                
        self.rotation_index = new_rotation
        self.current_piece = new_piece
        return True
        
    def can_move(self, dx, dy):
        """检查是否可以移动"""
        if not self.current_piece:
            return False
            
        for x, y in self.current_piece:
            new_x = self.piece_x + x + dx
            new_y = self.piece_y + y + dy
            if new_x < 0 or new_x >= self.BOARD_WIDTH or new_y >= self.BOARD_HEIGHT:
                return False
            if new_y >= 0 and self.board[new_y][new_x]:
                return False
        return True
        
    def place_piece(self):
        """固定当前方块到游戏板上"""
        if not self.current_piece:
            return
            
        for x, y in self.current_piece:
            board_x = self.piece_x + x
            board_y = self.piece_y + y
            if 0 <= board_x < self.BOARD_WIDTH and 0 <= board_y < self.BOARD_HEIGHT:
                self.board[board_y][board_x] = self.current_shape
                
    def check_lines(self):
        """检查并消除完整的行"""
        lines_cleared = 0
        y = self.BOARD_HEIGHT - 1
        while y >= 0:
            if all(self.board[y]):
                # 消除当前行
                for move_y in range(y, 0, -1):
                    self.board[move_y] = self.board[move_y - 1][:]
                self.board[0] = [None] * self.BOARD_WIDTH
                lines_cleared += 1
            else:
                y -= 1
                
        # 更新分数
        if lines_cleared > 0:
            self.score += (1 << lines_cleared) * 100
            self.level = self.score // 1000 + 1
            
    def draw_game(self):
        """绘制游戏画面"""
        # 清除现有游戏元素
        while len(self.game_group) > 0:
            self.game_group.pop()
            
        # 绘制游戏区域边框
        border = Rect(
            x=self.BOARD_X - 1,
            y=self.BOARD_Y - 1,
            width=self.BOARD_WIDTH * self.GRID_SIZE + 2,
            height=self.BOARD_HEIGHT * self.GRID_SIZE + 2,
            outline=self.colors['grid']
        )
        self.game_group.append(border)
        
        # 绘制网格
        for x in range(self.BOARD_WIDTH + 1):
            grid_line = Rect(
                x=self.BOARD_X + x * self.GRID_SIZE,
                y=self.BOARD_Y,
                width=1,
                height=self.BOARD_HEIGHT * self.GRID_SIZE,
                fill=self.colors['grid']
            )
            self.game_group.append(grid_line)
            
        for y in range(self.BOARD_HEIGHT + 1):
            grid_line = Rect(
                x=self.BOARD_X,
                y=self.BOARD_Y + y * self.GRID_SIZE,
                width=self.BOARD_WIDTH * self.GRID_SIZE,
                height=1,
                fill=self.colors['grid']
            )
            self.game_group.append(grid_line)
            
        # 绘制已放置的方块
        for y in range(self.BOARD_HEIGHT):
            for x in range(self.BOARD_WIDTH):
                if self.board[y][x]:
                    block = Rect(
                        x=self.BOARD_X + x * self.GRID_SIZE + 1,
                        y=self.BOARD_Y + y * self.GRID_SIZE + 1,
                        width=self.GRID_SIZE - 2,
                        height=self.GRID_SIZE - 2,
                        fill=self.colors[f'block_{self.board[y][x].lower()}']
                    )
                    self.game_group.append(block)
                    
        # 绘制当前方块
        if self.current_piece:
            for x, y in self.current_piece:
                block = Rect(
                    x=self.BOARD_X + (self.piece_x + x) * self.GRID_SIZE + 1,
                    y=self.BOARD_Y + (self.piece_y + y) * self.GRID_SIZE + 1,
                    width=self.GRID_SIZE - 2,
                    height=self.GRID_SIZE - 2,
                    fill=self.colors[f'block_{self.current_shape.lower()}']
                )
                self.game_group.append(block)
                
        # 更新分数
        self.score_label.text = f"Score: {self.score}"
        
        # 更新显示
        self.display.root_group = self.main_group
        
    def show_game_over(self):
        """显示游戏结束画面"""
        game_over_group = displayio.Group()
        
        # 绘制背景
        bg = Rect(
            x=0,
            y=0,
            width=self.display.width,
            height=self.display.height,
            fill=self.colors['background']
        )
        game_over_group.append(bg)
        
        # 显示游戏结束文本
        game_over_text = label.Label(
            terminalio.FONT,
            text="Game Over",
            color=self.colors['error'],
            anchor_point=(0.5, 0.5),
            anchored_position=(self.display.width // 2, self.display.height // 2 - 20)
        )
        game_over_group.append(game_over_text)
        
        # 显示最终分数
        score_text = label.Label(
            terminalio.FONT,
            text=f"Score: {self.score}",
            color=self.colors['text'],
            anchor_point=(0.5, 0.5),
            anchored_position=(self.display.width // 2, self.display.height // 2 + 10)
        )
        game_over_group.append(score_text)
        
        self.display.root_group = game_over_group
        time.sleep(2) 