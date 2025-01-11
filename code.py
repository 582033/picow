import time
import gc
import os
from pico.system import SystemManager

print("=== Pico System Starting ===")

# 初始化系统管理器
system = SystemManager()
system.print_system_info()

# 按需加载必要的模块
PicoDisplay = system.load_module('display')
PicoHardware = system.load_module('hardware')
Menu = system.load_module('menu')

if not all([PicoDisplay, PicoHardware, Menu]):
    print("Failed to load required modules")
    while True:
        time.sleep(1)

# 初始化显示屏和硬件
pico = PicoDisplay(tft_rotation=270)
hw = PicoHardware()

# 定义统一的颜色配置
colors = {
    'background': 0x000000,    # 黑色背景
    'text': 0x808080,          # 灰色未选中
    'selected': 0xFFFFFF,      # 白色选中文字
    'selected_bg': 0x202020,   # 深灰色选中背景
    'hint': 0x404040           # 深灰色提示
}

# 初始化菜单
menu = Menu(pico, hw, colors)

# 扫描应用目录
def scan_apps():
    """扫描应用目录"""
    apps = []
    try:
        app_dirs = [d for d in os.listdir("/apps") 
                   if d not in [".", ".."] and 
                   os.stat(f"/apps/{d}")[0] == 16384]
        app_dirs.sort()
        print(f"Found app directories: {app_dirs}")
        
        for app_dir in app_dirs:
            try:
                if "app.py" in os.listdir(f"/apps/{app_dir}"):
                    apps.append({
                        'name': app_dir[0].upper() + app_dir[1:].lower(),
                        'dir': app_dir,
                        'module_name': f"apps.{app_dir}.app"
                    })
                    print(f"Found app: {app_dir}")
            except Exception as e:
                print(f"Failed to scan app {app_dir}: {e}")
                
    except Exception as e:
        print(f"Error scanning apps: {e}")
        
    return apps if apps else [{'name': 'No Apps', 'dir': None, 'module_name': None}]

# 加载应用类
def load_app_class(app_info):
    """加载应用类"""
    try:
        if app_info['module_name'] is None:
            return None
            
        module = __import__(app_info['module_name'])
        for part in app_info['module_name'].split('.')[1:]:
            module = getattr(module, part)
            
        if hasattr(module, "APP_NAME"):
            app_info['name'] = module.APP_NAME
            
        return getattr(module, "App")
        
    except Exception as e:
        print(f"Error loading app {app_info['dir']}: {e}")
        return None

# 主循环
print("Starting main loop...")
while True:
    try:
        # 扫描应用
        apps = scan_apps()
        
        # 设置菜单项
        menu.set_menu_items(apps)
        
        # 显示菜单并等待选择
        selected = menu.show()
        if selected:
            # 加载并运行应用
            app_class = load_app_class(selected)
            if app_class:
                # 创建应用实例
                app = app_class(pico, hw, colors)
                
                # 运行应用
                app.play()
                
                # 应用退出后清理
                del app
                gc.collect()
                system.print_system_info()
                
    except Exception as e:
        print(f"Error in main loop: {e}")
        time.sleep(1)
        
    # 垃圾回收
    gc.collect()

