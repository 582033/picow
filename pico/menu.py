import time
import displayio
import terminalio
from adafruit_display_text import label
from adafruit_display_shapes.rect import Rect
from adafruit_display_shapes.roundrect import RoundRect

class Menu:
    def __new__(cls, *args, **kwargs):
        """单例模式"""
        if not hasattr(cls, '_instance'):
            cls._instance = super(Menu, cls).__new__(cls)
        return cls._instance
        
    def __init__(self, pico=None, hw=None, colors=None):
        """初始化菜单"""
        # 避免重复初始化
        if hasattr(self, '_initialized'):
            return
            
        if not all([pico, hw, colors]):
            return
            
        self.pico = pico
        self.hw = hw
        self.colors = colors
        self.display = pico.display
        
        # 菜单配置
        self.menu_items = []
        self.current_index = 0
        self.scroll_offset = 0
        
        # 显示配置
        self.item_height = 30
        self.item_padding = 5
        self.text_scale = 1
        self.visible_items = (self.display.height - 25) // self.item_height
        
        # 创建主显示组
        self.main_group = displayio.Group()
        
        # 创建背景
        self.bg_rect = Rect(
            x=0,
            y=0,
            width=self.display.width,
            height=self.display.height,
            fill=self.colors['background']
        )
        self.main_group.append(self.bg_rect)
        
        # 创建菜单项组
        self.menu_group = displayio.Group()
        self.main_group.append(self.menu_group)
        
        # 创建选中项高亮
        self.highlight = RoundRect(
            x=2,
            y=0,
            width=self.display.width - 4,
            height=self.item_height - 2,
            r=4,
            fill=self.colors['selected_bg']
        )
        self.menu_group.append(self.highlight)
        
        # 创建滚动指示器
        self.scroll_up = displayio.Group()
        self.scroll_down = displayio.Group()
        self.main_group.append(self.scroll_up)
        self.main_group.append(self.scroll_down)
        
        # 创建按键提示
        self.hints_group = displayio.Group()
        self.main_group.append(self.hints_group)
        self._add_button_hints()
        
    def _add_button_hints(self):
        """添加按键提示"""
        hints = [
            ("A:Select", 5),
            ("B:Back", self.display.width - 50)
        ]
        
        for text, x in hints:
            hint_label = label.Label(
                terminalio.FONT,
                text=text,
                color=self.colors['hint'],
                x=x,
                y=self.display.height - 15,
                scale=1
            )
            self.hints_group.append(hint_label)
        
    def set_menu_items(self, items):
        """设置菜单项"""
        self.menu_items = items
        self.current_index = 0
        self.scroll_offset = 0
        self.draw_menu()
        
    def draw_menu(self):
        """绘制菜单"""
        # 清除现有菜单项
        while len(self.menu_group) > 1:  # 保留highlight
            self.menu_group.pop()
            
        # 计算可见项范围
        start_idx = self.scroll_offset
        end_idx = min(start_idx + self.visible_items, len(self.menu_items))
        
        # 更新高亮位置
        visible_index = self.current_index - self.scroll_offset
        self.highlight.y = visible_index * self.item_height + 1
        
        # 绘制菜单项
        for i, item in enumerate(self.menu_items[start_idx:end_idx]):
            # 判断是否是选中项
            is_selected = (i + start_idx) == self.current_index
            text_color = self.colors['selected'] if is_selected else self.colors['text']
            
            text = label.Label(
                terminalio.FONT,
                text=item['name'],
                color=text_color,
                scale=self.text_scale,
                x=20,
                y=i * self.item_height + self.item_height // 2,
                anchor_point=(0, 0.5),
                anchored_position=(20, i * self.item_height + self.item_height // 2)
            )
            self.menu_group.append(text)
            
        # 更新滚动指示器
        self.update_scroll_indicators()
        
        # 更新显示
        self.display.root_group = self.main_group
        
    def update_scroll_indicators(self):
        """更新滚动指示器"""
        # 清除现有指示器
        while len(self.scroll_up) > 0:
            self.scroll_up.pop()
        while len(self.scroll_down) > 0:
            self.scroll_down.pop()
            
        # 显示向上滚动指示器
        if self.scroll_offset > 0:
            up_indicator = RoundRect(
                x=self.display.width - 15,
                y=5,
                width=10,
                height=5,
                r=2,
                fill=self.colors['hint']
            )
            self.scroll_up.append(up_indicator)
            
        # 显示向下滚动指示器
        if self.scroll_offset + self.visible_items < len(self.menu_items):
            down_indicator = RoundRect(
                x=self.display.width - 15,
                y=self.display.height - 30,
                width=10,
                height=5,
                r=2,
                fill=self.colors['hint']
            )
            self.scroll_down.append(down_indicator)
            
    def handle_input(self):
        """处理输入"""
        if self.hw.get_button_state('up'):
            if self.current_index > 0:
                self.current_index -= 1
                if self.current_index < self.scroll_offset:
                    self.scroll_offset = self.current_index
                self.draw_menu()
            time.sleep(0.2)
            
        elif self.hw.get_button_state('down'):
            if self.current_index < len(self.menu_items) - 1:
                self.current_index += 1
                if self.current_index >= self.scroll_offset + self.visible_items:
                    self.scroll_offset = self.current_index - self.visible_items + 1
                self.draw_menu()
            time.sleep(0.2)
            
        elif self.hw.get_button_state('a'):
            if 0 <= self.current_index < len(self.menu_items):
                return self.menu_items[self.current_index]
            time.sleep(0.2)
            
        return None
        
    def show(self):
        """显示菜单并处理输入"""
        self.draw_menu()
        while True:
            selected = self.handle_input()
            if selected:
                try:
                    # 运行选中的应用
                    app_module = selected.get('module')
                    if app_module:
                        # 清理之前的模块
                        from pico.system import SystemManager
                        system = SystemManager()
                        system.cleanup_all()
                        
                        # 运行新应用
                        app = app_module(self.display, self.hw, self.colors)
                        result = app.play()
                        
                        # 应用退出后清理
                        system.cleanup_all()
                        
                        # 重新显示菜单
                        self.draw_menu()
                        continue
                except Exception as e:
                    print(f"Error running app: {e}")
                    # 发生错误时也要清理
                    from pico.system import SystemManager
                    SystemManager().cleanup_all()
                return selected
            time.sleep(0.01)  # 防止CPU占用过高

    def cleanup_modules(self):
        """清理不需要的模块"""
        print("\n=== Cleaning up modules ===")
        import sys
        import gc
        
        # 查找需要清理的模块
        modules_to_remove = []
        for module_name in list(sys.modules.keys()):
            # 清理 apps 下的模块
            if module_name.startswith('apps.'):
                modules_to_remove.append(module_name)
        
        # 清理模块
        for module_name in modules_to_remove:
            try:
                print(f"Removing module: {module_name}")
                if module_name in sys.modules:
                    # 如果模块有cleanup方法，先调用它
                    module = sys.modules[module_name]
                    if hasattr(module, 'cleanup'):
                        try:
                            module.cleanup()
                        except:
                            pass
                    # 删除模块
                    del sys.modules[module_name]
            except Exception as e:
                print(f"Error removing module {module_name}: {e}")
        
        # 执行垃圾回收
        gc.collect()
        print("=== Cleanup complete ===\n") 