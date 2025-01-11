import board
import pwmio
import time

class PicoBuzzer:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            print("Initializing PicoBuzzer...")
            cls._instance = super(PicoBuzzer, cls).__new__(cls)
        return cls._instance
        
    def __init__(self):
        if not self._initialized:
            try:
                self.buzzer = pwmio.PWMOut(board.GP5, frequency=440, duty_cycle=0, variable_frequency=True)
                self._initialized = True
                print("Buzzer initialized successfully")
            except Exception as e:
                print(f"Error initializing buzzer: {e}")
                self.buzzer = None
                
    def play_tone(self, frequency, duration=0.1):
        """播放指定频率的音调"""
        if self.buzzer is None:
            return
            
        try:
            self.buzzer.frequency = int(frequency)  # 确保频率是整数
            self.buzzer.duty_cycle = 32768  # 50% duty cycle
            if duration > 0:
                time.sleep(duration)
                self.stop()
        except Exception as e:
            print(f"Error playing tone: {e}")
            
    def stop(self):
        """停止播放"""
        if self.buzzer is None:
            return
            
        try:
            self.buzzer.duty_cycle = 0
        except Exception as e:
            print(f"Error stopping buzzer: {e}")
            
    def play_from_file(self, file_path, check_interrupt=None, speed_factor=0.25):
        """从文件播放音乐
        
        Args:
            file_path: 音乐文件路径
            check_interrupt: 检查是否中断的回调函数
            speed_factor: 速度因子，值越小播放越快，默认0.25
        """
        if self.buzzer is None:
            return False
            
        try:
            with open(file_path, "r") as f:
                notes = f.readlines()
                
            # 解析音乐文件
            for note in notes:
                note = note.strip()
                if not note or note.startswith("#"):
                    continue
                    
                # 检查是否需要中断
                if check_interrupt and check_interrupt():
                    self.stop()
                    return False
                    
                try:
                    # 解析音符和时值
                    parts = note.split()
                    if len(parts) != 2:
                        continue
                        
                    note_name, duration = parts
                    
                    # 将音符转换为频率
                    frequency = self._note_to_frequency(note_name)
                    if frequency > 0:
                        self.play_tone(frequency, float(duration) * speed_factor)  # 使用速度因子调整播放速度
                    else:
                        time.sleep(float(duration) * speed_factor)  # 休止符也使用速度因子
                        
                except Exception as e:
                    print(f"Error playing note {note}: {e}")
                    continue
                    
            self.stop()
            return True
            
        except Exception as e:
            print(f"Error playing music from file {file_path}: {e}")
            self.stop()
            return False
            
    def _note_to_frequency(self, note):
        """将音符转换为频率"""
        try:
            if note == "R":  # 休止符
                return 0
                
            # 基本音符到频率的映射（使用整数频率）
            base_freq = {
                'C': 262,  # C4 (中央C)
                'D': 294,
                'E': 330,
                'F': 349,
                'G': 392,
                'A': 440,
                'B': 494
            }
            
            # 解析音符
            note_name = note[0].upper()
            octave = int(note[-1])
            
            # 计算频率
            freq = base_freq[note_name]
            # 根据八度调整频率
            freq = int(freq * (2 ** (octave - 4)))
            
            return freq
            
        except Exception as e:
            print(f"Error converting note {note} to frequency: {e}")
            return 0
