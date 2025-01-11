import time
import displayio
import gc

class Animation:
    def __init__(self, display):
        """初始化动画控制器"""
        self.display = display
        self._frame_delay = 0.05  # 默认帧率20fps
        self._current_animation = None
        self._is_playing = False

    def set_frame_rate(self, fps):
        """设置帧率"""
        if not 1 <= fps <= 60:
            raise ValueError("FPS must be between 1 and 60")
        self._frame_delay = 1.0 / fps

    def preload_images(self, image_list):
        """预加载图片序列"""
        try:
            print("Preloading images...")
            image_grids = []
            for img_path in image_list:
                try:
                    bitmap = displayio.OnDiskBitmap(open(img_path, "rb"))
                    grid = displayio.TileGrid(
                        bitmap,
                        pixel_shader=bitmap.pixel_shader,
                        x=0,
                        y=0
                    )
                    image_grids.append(grid)
                except Exception as e:
                    print(f"Error loading image {img_path}: {e}")
            print(f"Successfully loaded {len(image_grids)} images")
            return image_grids
        except Exception as e:
            print(f"Error in preload_images: {e}")
            return []

    def play_sequence(self, image_list, loop=True, check_button_callback=None):
        """播放图片序列"""
        try:
            # 预加载图片
            image_grids = self.preload_images(image_list)
            if not image_grids:
                print("No images to play")
                return False

            # 创建显示组
            group1 = displayio.Group()
            group2 = displayio.Group()
            
            # 添加背景
            group1.append(self.display.get_bgcolor_group())
            group2.append(self.display.get_bgcolor_group())

            # 开始播放循环
            self._is_playing = True
            current_group = group1
            
            print("Starting animation sequence...")
            while self._is_playing:
                for grid in image_grids:
                    try:
                        # 检查退出条件
                        if check_button_callback and check_button_callback():
                            self._is_playing = False
                            break

                        # 切换显示组
                        next_group = group2 if current_group == group1 else group1
                        
                        # 清除旧内容
                        while len(next_group) > 1:
                            next_group.pop()
                        
                        # 添加新图片
                        next_group.append(grid)
                        
                        # 切换显示
                        self.display.display.root_group = next_group
                        current_group = next_group
                        
                        # 延时
                        time.sleep(self._frame_delay)
                        
                        # 垃圾回收
                        gc.collect()
                        
                    except Exception as e:
                        print(f"Error in animation loop: {e}")
                        time.sleep(0.1)
                
                if not loop:
                    break

            return True

        except Exception as e:
            print(f"Error in play_sequence: {e}")
            return False

    def stop(self):
        """停止当前动画"""
        self._is_playing = False

    def fade_transition(self, from_image, to_image, duration=1.0):
        """渐变过渡效果"""
        try:
            steps = int(duration / self._frame_delay)
            for i in range(steps):
                alpha = i / steps
                # TODO: 实现渐变效果
                time.sleep(self._frame_delay)
        except Exception as e:
            print(f"Error in fade_transition: {e}")

    def slide_transition(self, from_image, to_image, direction="left", duration=0.5):
        """滑动过渡效果"""
        try:
            steps = int(duration / self._frame_delay)
            for i in range(steps):
                progress = i / steps
                # TODO: 实现滑动效果
                time.sleep(self._frame_delay)
        except Exception as e:
            print(f"Error in slide_transition: {e}")

    def cleanup(self):
        """清理资源"""
        self.stop()
        gc.collect() 