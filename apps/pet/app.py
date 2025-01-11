import time
import random
import displayio
import terminalio
from adafruit_display_text.label import Label
from adafruit_display_shapes.rect import Rect
from adafruit_display_shapes.circle import Circle
from adafruit_display_shapes.triangle import Triangle

# 应用名称，将显示在菜单中
APP_NAME = "VirtualPet"

class Pet:
    """宠物类，管理宠物的状态和动画"""
    def __init__(self, x, y, colors):
        self.x = x
        self.y = y
        self.colors = colors
        self.happiness = 80  # 初始快乐度
        self.hunger = 20     # 初始饥饿度
        self.energy = 100    # 初始能量
        self.exp = 0        # 经验值
        self.level = 1      # 等级
        self.state = 'normal'  # 状态：normal, eating, sleeping, playing
        self.animation_frame = 0
        self.last_update = time.monotonic()
        self.last_state_change = time.monotonic()
        
    def update(self):
        """更新宠物状态"""
        current_time = time.monotonic()
        
        # 每30秒更新一次基础状态
        if current_time - self.last_update >= 30:
            self.hunger = min(100, self.hunger + 5)
            self.energy = max(0, self.energy - 3)
            self.happiness = max(0, self.happiness - 2)
            self.last_update = current_time
            
        # 状态影响
        if self.hunger > 80:
            self.happiness = max(0, self.happiness - 5)
        if self.energy < 20:
            self.happiness = max(0, self.happiness - 5)
            
        # 自动切换回普通状态
        if current_time - self.last_state_change >= 3 and self.state != 'normal':
            self.state = 'normal'
            
        # 动画帧更新
        self.animation_frame = (self.animation_frame + 1) % 3
        
    def feed(self):
        """喂食"""
        if self.hunger <= 20:
            return False
        self.hunger = max(0, self.hunger - 30)
        self.happiness = min(100, self.happiness + 10)
        self.exp += 5
        self.state = 'eating'
        self.last_state_change = time.monotonic()
        return True
        
    def play(self):
        """玩耍"""
        if self.energy <= 10:
            return False
        self.energy = max(0, self.energy - 20)
        self.happiness = min(100, self.happiness + 20)
        self.hunger = min(100, self.hunger + 10)
        self.exp += 10
        self.state = 'playing'
        self.last_state_change = time.monotonic()
        return True
        
    def sleep(self):
        """睡觉"""
        if self.energy >= 90:
            return False
        self.energy = min(100, self.energy + 40)
        self.state = 'sleeping'
        self.last_state_change = time.monotonic()
        return True
        
    def check_level_up(self):
        """检查是否升级"""
        required_exp = self.level * 100
        if self.exp >= required_exp:
            self.level += 1
            self.exp -= required_exp
            return True
        return False
        
    def draw(self, group):
        """绘制像素风格蔡徐坤打篮球动画"""
        # 清除旧的显示元素
        while len(group) > 0:
            group.pop()
            
        # 颜色定义
        skin = 0xFCD8B4     # 肤色
        black = 0x000000    # 黑色（描边）
        white = 0xFFFFFF    # 白色（裤子和背带）
        orange = 0xFFA500   # 橙色（篮球）
        gray = 0x808080     # 灰色（头发）
        yellow = 0xFFFF00   # 黄色（特效）
        blue = 0x6495ED     # 蓝色（毯子）

        if self.state == 'eating':
            # 吃东西动画 - 坐着吃鸡腿
            # 白色裤子（坐姿）
            pants = Rect(self.x - 15, self.y + 5, 30, 12, fill=white)
            group.append(pants)
            
            # 黑色上衣（坐姿）
            shirt = Rect(self.x - 12, self.y - 5, 24, 15, fill=black)
            group.append(shirt)
            
            # Y字型白色背带
            strap_left = Rect(self.x - 8, self.y - 5, 3, 20, fill=white)
            strap_right = Rect(self.x + 5, self.y - 5, 3, 20, fill=white)
            strap_middle = Rect(self.x - 2, self.y - 5, 4, 8, fill=white)
            group.append(strap_left)
            group.append(strap_right)
            group.append(strap_middle)
            
            # 头部（肤色）
            head = Rect(self.x - 10, self.y - 25, 20, 20, fill=skin)
            group.append(head)
            
            # 灰色大分头发型
            hair_main = Rect(self.x - 8, self.y - 28, 16, 8, fill=gray)
            hair_part = Rect(self.x - 2, self.y - 28, 4, 12, fill=gray)
            hair_left = Rect(self.x - 8, self.y - 25, 4, 15, fill=gray)
            hair_right = Rect(self.x + 4, self.y - 25, 4, 15, fill=gray)
            group.append(hair_main)
            group.append(hair_part)
            group.append(hair_left)
            group.append(hair_right)
            
            # 手臂（拿着鸡腿）
            arm = Rect(self.x + 10, self.y - 2, 5, 12, fill=skin)
            group.append(arm)
            
            # 鸡腿
            chicken = Circle(self.x + 18, self.y + 2, 6, fill=0xCD853F)
            bone = Rect(self.x + 22, self.y - 2, 2, 8, fill=white)
            group.append(chicken)
            group.append(bone)
            
            # 表情（开心吃东西）
            eye_left = Circle(self.x - 6, self.y - 15, 2, fill=black)
            eye_right = Circle(self.x + 6, self.y - 15, 2, fill=black)
            # 张开的嘴
            mouth = Circle(self.x, self.y - 8, 3, fill=black)
            
            # 添加音符特效
            if self.animation_frame % 2 == 0:
                note = Label(terminalio.FONT, text="♪", color=yellow, x=self.x - 15, y=self.y - 20)
                group.append(note)
            
        elif self.state == 'playing':
            # 打篮球动画
            if self.animation_frame == 0:  # 准备姿势
                # 标准站立姿势代码...
                self._draw_standing_pose(group)
                # 篮球在手中
                ball = Circle(self.x + 15, self.y, 6, fill=orange)
                ball_lines = [
                    Rect(self.x + 12, self.y, 6, 1, fill=black),
                    Rect(self.x + 15, self.y - 3, 1, 6, fill=black)
                ]
                group.append(ball)
                for line in ball_lines:
                    group.append(line)
                    
            elif self.animation_frame == 1:  # 投篮动作
                # 投篮姿势代码...
                self._draw_shooting_pose(group)
                # 篮球上升
                ball = Circle(self.x + 10, self.y - 15, 6, fill=orange)
                ball_lines = [
                    Rect(self.x + 7, self.y - 15, 6, 1, fill=black),
                    Rect(self.x + 10, self.y - 18, 1, 6, fill=black)
                ]
                group.append(ball)
                for line in ball_lines:
                    group.append(line)
                
            else:  # 收手动作
                # 收手姿势代码...
                self._draw_follow_through_pose(group)
                # 篮球最高点
                ball = Circle(self.x, self.y - 30, 6, fill=orange)
                ball_lines = [
                    Rect(self.x - 3, self.y - 30, 6, 1, fill=black),
                    Rect(self.x, self.y - 33, 1, 6, fill=black)
                ]
                group.append(ball)
                for line in ball_lines:
                    group.append(line)
                    
            # 添加动作特效
            if self.animation_frame % 2 == 0:
                star1 = Circle(self.x + 25, self.y - 15, 3, fill=yellow)
                star2 = Circle(self.x - 20, self.y - 10, 2, fill=yellow)
                group.append(star1)
                group.append(star2)
            
        elif self.state == 'sleeping':
            # 睡觉动画 - 侧躺
            # 黑色描边
            outline_blocks = [
                # 身体轮廓
                Rect(self.x - 25, self.y - 15, 50, 30, fill=black),
            ]
            for block in outline_blocks:
                group.append(block)
            
            # 白色裤子（侧躺）
            pants_blocks = [
                Rect(self.x - 23, self.y + 5, 30, 8, fill=white),
            ]
            for block in pants_blocks:
                group.append(block)
            
            # 黑色上衣（侧躺）
            shirt = Rect(self.x - 23, self.y - 3, 30, 8, fill=black)
            group.append(shirt)
            
            # Y字型白色背带（侧躺）
            strap_blocks = [
                Rect(self.x - 18, self.y - 3, 25, 3, fill=white),  # 横向背带
                Rect(self.x + 2, self.y - 3, 3, 16, fill=white)    # 竖向背带
            ]
            for block in strap_blocks:
                group.append(block)
            
            # 头部（侧躺，带描边）
            head_outline = Rect(self.x - 23, self.y - 13, 22, 18, fill=black)
            head = Rect(self.x - 22, self.y - 12, 20, 16, fill=skin)
            group.append(head_outline)
            group.append(head)
            
            # 灰色头发（侧躺）
            hair_blocks = [
                Rect(self.x - 20, self.y - 15, 16, 6, fill=gray),  # 主要发型
                Rect(self.x - 22, self.y - 12, 4, 10, fill=gray),  # 侧面头发
            ]
            for block in hair_blocks:
                group.append(block)
            
            # 闭眼睡觉表情
            eye = Rect(self.x - 18, self.y - 8, 6, 2, fill=black)
            mouth = Rect(self.x - 15, self.y - 4, 4, 2, fill=black)
            group.append(eye)
            group.append(mouth)
            
            # 添加睡觉特效
            if self.animation_frame % 3 == 0:
                z1 = Label(terminalio.FONT, text="z", color=gray, x=self.x - 5, y=self.y - 20)
                z2 = Label(terminalio.FONT, text="Z", color=gray, x=self.x + 5, y=self.y - 25)
                z3 = Label(terminalio.FONT, text="Z", color=gray, x=self.x + 15, y=self.y - 30)
                group.append(z1)
                group.append(z2)
                group.append(z3)
            
            # 添加小毯子（像素风格）
            blanket_blocks = [
                Rect(self.x - 23, self.y + 2, 35, 15, fill=blue),  # 主体
                Rect(self.x - 20, self.y + 5, 30, 2, fill=0x4169E1),  # 花纹1
                Rect(self.x - 20, self.y + 10, 30, 2, fill=0x4169E1), # 花纹2
            ]
            for block in blanket_blocks:
                group.append(block)
                
        else:  # 正常状态
            # 标准站立姿势
            self._draw_standing_pose(group)
            
        # 添加面部表情（除了睡觉状态）
        if self.state != 'sleeping':
            eye_left = Rect(self.x - 6, self.y - 15, 3, 2, fill=black)
            eye_right = Rect(self.x + 3, self.y - 15, 3, 2, fill=black)
            mouth = Rect(self.x - 4, self.y - 10, 8, 2, fill=black)
            group.append(eye_left)
            group.append(eye_right)
            group.append(mouth)
            
    def _draw_standing_pose(self, group):
        """绘制标准站立姿势"""
        # 白色裤子
        pants = Rect(self.x - 12, self.y + 5, 24, 15, fill=0xFFFFFF)
        group.append(pants)
        
        # 黑色上衣
        shirt = Rect(self.x - 12, self.y - 5, 24, 15, fill=0x000000)
        group.append(shirt)
        
        # Y字型白色背带
        strap_left = Rect(self.x - 8, self.y - 5, 3, 20, fill=0xFFFFFF)
        strap_right = Rect(self.x + 5, self.y - 5, 3, 20, fill=0xFFFFFF)
        strap_middle = Rect(self.x - 2, self.y - 5, 4, 8, fill=0xFFFFFF)
        group.append(strap_left)
        group.append(strap_right)
        group.append(strap_middle)
        
        # 肤色胳膊
        arm_left = Rect(self.x - 15, self.y - 2, 5, 12, fill=0xFCD8B4)
        arm_right = Rect(self.x + 10, self.y - 2, 5, 12, fill=0xFCD8B4)
        group.append(arm_left)
        group.append(arm_right)
        
        # 头部和头发
        head = Rect(self.x - 10, self.y - 25, 20, 20, fill=0xFCD8B4)
        hair_main = Rect(self.x - 8, self.y - 28, 16, 8, fill=0x808080)
        hair_part = Rect(self.x - 2, self.y - 28, 4, 12, fill=0x808080)
        hair_left = Rect(self.x - 8, self.y - 25, 4, 15, fill=0x808080)
        hair_right = Rect(self.x + 4, self.y - 25, 4, 15, fill=0x808080)
        group.append(head)
        group.append(hair_main)
        group.append(hair_part)
        group.append(hair_left)
        group.append(hair_right)
        
    def _draw_shooting_pose(self, group):
        """绘制投篮姿势"""
        # 黑色描边
        outline_blocks = [
            # 身体轮廓
            Rect(self.x - 13, self.y - 26, 26, 50, fill=0x000000),
            # 手臂轮廓
            Rect(self.x - 16, self.y - 3, 7, 14, fill=0x000000),
            Rect(self.x + 9, self.y - 3, 7, 20, fill=0x000000)  # 右臂抬高
        ]
        for block in outline_blocks:
            group.append(block)
        
        # 白色裤子（大像素块，前倾）
        pants_blocks = [
            Rect(self.x - 12, self.y + 8, 10, 15, fill=0xFFFFFF),
            Rect(self.x + 2, self.y + 8, 10, 15, fill=0xFFFFFF)
        ]
        for block in pants_blocks:
            group.append(block)
        
        # 黑色上衣（大像素块，前倾）
        shirt = Rect(self.x - 12, self.y - 2, 24, 10, fill=0x000000)
        group.append(shirt)
        
        # Y字型白色背带（前倾）
        strap_blocks = [
            Rect(self.x - 8, self.y - 2, 4, 20, fill=0xFFFFFF),  # 左竖
            Rect(self.x + 4, self.y - 2, 4, 20, fill=0xFFFFFF),  # 右竖
            Rect(self.x - 2, self.y - 2, 4, 6, fill=0xFFFFFF)    # 中间连接
        ]
        for block in strap_blocks:
            group.append(block)
        
        # 肤色胳膊（投篮姿势）
        arm_left = Rect(self.x - 15, self.y, 5, 12, fill=0xFCD8B4)  # 左臂略微下垂
        arm_right = Rect(self.x + 10, self.y - 10, 5, 18, fill=0xFCD8B4)  # 右臂抬高
        group.append(arm_left)
        group.append(arm_right)
        
        # 头部（前倾，带描边）
        head_outline = Rect(self.x - 11, self.y - 22, 22, 20, fill=0x000000)
        head = Rect(self.x - 10, self.y - 21, 20, 18, fill=0xFCD8B4)
        group.append(head_outline)
        group.append(head)
        
        # 灰色头发（前倾）
        hair_blocks = [
            Rect(self.x - 9, self.y - 25, 18, 8, fill=0x808080),  # 主要发型
            Rect(self.x - 9, self.y - 21, 5, 12, fill=0x808080),  # 左侧头发
            Rect(self.x + 4, self.y - 21, 5, 12, fill=0x808080)   # 右侧头发
        ]
        for block in hair_blocks:
            group.append(block)
            
        # 眼睛（专注表情）
        eye_left = Rect(self.x - 7, self.y - 13, 4, 4, fill=0x000000)
        eye_right = Rect(self.x + 3, self.y - 13, 4, 4, fill=0x000000)
            group.append(eye_left)
            group.append(eye_right)
        
        # 嘴巴（咬牙表情）
        mouth = Rect(self.x - 5, self.y - 7, 10, 2, fill=0x000000)
        group.append(mouth)

    def _draw_follow_through_pose(self, group):
        """绘制收手姿势"""
        # 黑色描边
        outline_blocks = [
            # 身体轮廓
            Rect(self.x - 13, self.y - 26, 26, 50, fill=0x000000),
            # 手臂轮廓
            Rect(self.x - 16, self.y + 2, 7, 14, fill=0x000000),
            Rect(self.x + 9, self.y - 15, 7, 25, fill=0x000000)  # 右臂完全抬起
        ]
        for block in outline_blocks:
            group.append(block)
        
        # 白色裤子（大像素块，后仰）
        pants_blocks = [
            Rect(self.x - 12, self.y + 10, 10, 15, fill=0xFFFFFF),
            Rect(self.x + 2, self.y + 10, 10, 15, fill=0xFFFFFF)
        ]
        for block in pants_blocks:
            group.append(block)
        
        # 黑色上衣（大像素块，后仰）
        shirt = Rect(self.x - 12, self.y, 24, 10, fill=0x000000)
        group.append(shirt)
        
        # Y字型白色背带（后仰）
        strap_blocks = [
            Rect(self.x - 8, self.y, 4, 20, fill=0xFFFFFF),  # 左竖
            Rect(self.x + 4, self.y, 4, 20, fill=0xFFFFFF),  # 右竖
            Rect(self.x - 2, self.y, 4, 6, fill=0xFFFFFF)    # 中间连接
        ]
        for block in strap_blocks:
            group.append(block)
        
        # 肤色胳膊（收手姿势）
        arm_left = Rect(self.x - 15, self.y + 2, 5, 12, fill=0xFCD8B4)  # 左臂下垂
        arm_right = Rect(self.x + 10, self.y - 15, 5, 20, fill=0xFCD8B4)  # 右臂完全抬起
        group.append(arm_left)
        group.append(arm_right)
        
        # 头部（后仰，带描边）
        head_outline = Rect(self.x - 11, self.y - 20, 22, 20, fill=0x000000)
        head = Rect(self.x - 10, self.y - 19, 20, 18, fill=0xFCD8B4)
        group.append(head_outline)
        group.append(head)
        
        # 灰色头发（后仰）
        hair_blocks = [
            Rect(self.x - 9, self.y - 23, 18, 8, fill=0x808080),  # 主要发型
            Rect(self.x - 9, self.y - 19, 5, 12, fill=0x808080),  # 左侧头发
            Rect(self.x + 4, self.y - 19, 5, 12, fill=0x808080)   # 右侧头发
        ]
        for block in hair_blocks:
            group.append(block)
            
        # 眼睛（兴奋表情）
        eye_left = Rect(self.x - 7, self.y - 11, 4, 4, fill=0x000000)
        eye_right = Rect(self.x + 3, self.y - 11, 4, 4, fill=0x000000)
        group.append(eye_left)
        group.append(eye_right)
        
        # 嘴巴（兴奋表情）
        mouth = Rect(self.x - 5, self.y - 5, 10, 3, fill=0x000000)
        group.append(mouth)
        
class App:
    def __init__(self, pico, hw, colors):
        self.pico = pico
        self.hw = hw
        self.display = pico.display
        self.colors = colors
        
        # 创建显示组
        self.main_group = displayio.Group()
        self.pet_group = displayio.Group()
        self.status_group = displayio.Group()
        self.main_group.append(self.pet_group)
        self.main_group.append(self.status_group)
        
        # 创建宠物实例
        self.pet = Pet(
            self.display.width // 2,
            self.display.height // 2,
            colors
        )
        
        # 创建状态标签
        self.status_labels = {
            'happiness': self.create_label("Happy:", 5, 10),
            'hunger': self.create_label("Hunger:", 5, 25),
            'energy': self.create_label("Energy:", 5, 40),
            'level': self.create_label("Level:", 5, 55),
        }
        for label in self.status_labels.values():
            self.status_group.append(label)
            
        # 创建操作提示
        hints = [
            ("A:Feed", 5),  # 最左
            ("UP:Play", 60),  # 中左
            ("DOWN:Sleep", self.display.width // 2 - 10),  # 中间
            ("B:Back", self.display.width - 40)  # 最右
        ]
        for text, x in hints:
            hint = Label(
                terminalio.FONT,
                text=text,
                color=self.colors['hint'],
                x=x,
                y=self.display.height - 15
            )
            self.status_group.append(hint)
            
        # 添加状态追踪
        self.last_pet_state = None
        self.last_animation_frame = None
        self.last_stats = {
            'happiness': -1,
            'hunger': -1,
            'energy': -1,
            'level': -1
        }
        self.last_update_time = time.monotonic()
        self.animation_update_time = time.monotonic()
        
    def create_label(self, text, x, y):
        """创建状态标签"""
        return Label(
            terminalio.FONT,
            text=text,
            color=self.colors['text'],
            x=x,
            y=y
        )
        
    def update_status_display(self):
        """更新状态显示"""
        # 只在数值发生变化时更新显示
        current_stats = {
            'happiness': self.pet.happiness,
            'hunger': self.pet.hunger,
            'energy': self.pet.energy,
            'level': self.pet.level
        }
        
        status_names = {
            'happiness': 'Happy',
            'hunger': 'Hunger',
            'energy': 'Energy',
            'level': 'Level'
        }
        
        for key, value in current_stats.items():
            if value != self.last_stats[key]:
                self.last_stats[key] = value
                self.status_labels[key].text = f"{status_names[key]}: {value}%"
                
    def show_notification(self, text, duration=1.0):
        """显示通知"""
        notification = Label(
            terminalio.FONT,
            text=text,
            color=self.colors['selected'],
            anchor_point=(0.5, 0.5),
            anchored_position=(self.display.width // 2, self.display.height // 2 - 40)
        )
        self.status_group.append(notification)
        time.sleep(duration)
        self.status_group.remove(notification)
        
    def play(self):
        """运行游戏"""
        # 设置显示
        self.display.root_group = self.main_group
        
        # 初始绘制
        self.pet.draw(self.pet_group)
        self.update_status_display()
        
        while True:
            current_time = time.monotonic()
            
            try:
                # 处理按键输入
                if self.hw.get_button_state('a'):  # 喂食
                    if self.pet.feed():
                        self.show_notification("Yummy!")
                    else:
                        self.show_notification("Not hungry!")
                    time.sleep(0.2)
                    
                elif self.hw.get_button_state('up'):  # 玩耍
                    if self.pet.play():
                        self.show_notification("Fun!")
                    else:
                        self.show_notification("Too tired!")
                    time.sleep(0.2)
                    
                elif self.hw.get_button_state('down'):  # 睡觉
                    if self.pet.sleep():
                        self.show_notification("ZZZ...")
                    else:
                        self.show_notification("Not sleepy!")
                    time.sleep(0.2)
                    
                elif self.hw.get_button_state('b'):  # 返回
                    return True
                
                # 每1秒更新一次状态
                if current_time - self.last_update_time >= 1.0:
                    self.pet.update()
                    self.update_status_display()
                    self.last_update_time = current_time
                    
                # 每0.5秒更新一次动画
                if current_time - self.animation_update_time >= 0.5:
                    # 只在状态改变或动画帧更新时重绘
                    if (self.last_pet_state != self.pet.state or 
                        self.last_animation_frame != self.pet.animation_frame):
                        self.pet.draw(self.pet_group)
                        self.last_pet_state = self.pet.state
                        self.last_animation_frame = self.pet.animation_frame
                    self.animation_update_time = current_time
                    
            except Exception as e:
                print(f"Error in button handling: {str(e)}")
                
            time.sleep(0.01)  # 防止CPU占用过高 