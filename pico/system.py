import os
import gc
import time
import microcontroller
import storage

class SystemManager:
    def __init__(self):
        self._init_time = time.monotonic()
        self._modules = {}
        
    def get_system_info(self):
        """获取系统信息"""
        try:
            # CPU信息
            cpu_temp = microcontroller.cpu.temperature
            cpu_freq = microcontroller.cpu.frequency
            
            # 内存信息
            gc.collect()  # 先进行垃圾回收
            mem_free = gc.mem_free()
            mem_alloc = gc.mem_alloc()
            mem_total = mem_free + mem_alloc
            
            # 磁盘信息
            try:
                fs_stat = os.statvfs('/')
                flash_size = fs_stat[0] * fs_stat[2]  # 总大小
                flash_free = fs_stat[0] * fs_stat[3]  # 可用空间
            except:
                flash_size = 0
                flash_free = 0
            
            # 运行时间
            uptime = time.monotonic() - self._init_time
            
            return {
                'cpu': {
                    'temperature': f"{cpu_temp:.1f}°C",
                    'frequency': f"{cpu_freq/1000000:.0f}MHz"
                },
                'memory': {
                    'total': mem_total,
                    'free': mem_free,
                    'used': mem_alloc,
                    'usage': f"{(mem_alloc/mem_total*100):.1f}%"
                },
                'storage': {
                    'total': flash_size,
                    'free': flash_free,
                    'usage': f"{((flash_size-flash_free)/flash_size*100):.1f}%"
                },
                'uptime': f"{int(uptime)}s"
            }
        except Exception as e:
            print(f"Error getting system info: {e}")
            return None
            
    def print_system_info(self):
        """打印系统信息"""
        info = self.get_system_info()
        if info:
            print("\n=== System Information ===")
            print(f"CPU Temp: {info['cpu']['temperature']}")
            print(f"CPU Freq: {info['cpu']['frequency']}")
            print(f"Memory: {info['memory']['free']}/{info['memory']['total']} bytes ({info['memory']['usage']})")
            print(f"Storage: {info['storage']['free']}/{info['storage']['total']} bytes ({info['storage']['usage']})")
            print(f"Uptime: {info['uptime']}")
            print("=======================\n")
            
    def cleanup(self):
        """清理系统资源"""
        gc.collect()
        self.print_system_info()
        
    def load_module(self, module_name):
        """按需加载模块"""
        if module_name not in self._modules:
            try:
                # 动态导入模块
                if module_name == 'display':
                    from pico.display import PicoDisplay as Module
                elif module_name == 'hardware':
                    from pico.hardware import PicoHardware as Module
                elif module_name == 'menu':
                    from pico.menu import Menu as Module
                else:
                    print(f"Unknown module: {module_name}")
                    return None
                    
                self._modules[module_name] = Module
                print(f"Loaded module: {module_name}")
                return Module
            except Exception as e:
                print(f"Error loading module {module_name}: {e}")
                return None
        return self._modules[module_name]
        
    def unload_module(self, module_name):
        """卸载模块"""
        if module_name in self._modules:
            try:
                # 如果模块有cleanup方法，调用它
                module = self._modules[module_name]
                if hasattr(module, 'cleanup'):
                    module.cleanup()
                del self._modules[module_name]
                gc.collect()  # 强制垃圾回收
            except Exception as e:
                print(f"Error unloading module {module_name}: {e}")
                
    def get_hardware_info(self):
        """获取硬件信息"""
        return {
            'display': {
                'width': 240,
                'height': 135,
                'pins': {
                    'dc': 'GP8',
                    'cs': 'GP9',
                    'clk': 'GP10',
                    'mosi': 'GP11',
                    'rst': 'GP12',
                    'bl': 'GP13'
                }
            },
            'buttons': {
                'up': 'GP2',
                'down': 'GP18',
                'left': 'GP16',
                'right': 'GP20',
                'center': 'GP3',
                'a': 'GP15',
                'b': 'GP17'
            },
            'buzzer': 'GP22'
        } 