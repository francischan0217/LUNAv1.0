import logging
import threading
import time

from xiaozhi.src.display.base_display import BaseDisplay
from typing import Optional, Callable

logger = logging.getLogger("FuncDisplay")
record_path = "text.wav"

class FuncDisplay(BaseDisplay):

    def __init__(self):

        super().__init__() # 调用父类初始化

        """初始化Func显示"""
        self.logger = logging.getLogger("FuncDisplay")
        self.running = True

        # Initialize Status
        self.current_status = "未连接"
        self.current_text = "待命"
        self.current_emotion = "😊"

        # Initialize Callback
        self.auto_callback = None
        self.status_callback = None
        self.text_callback = None
        self.emotion_callback = None
        self.abort_callback = None

        # Initialize Button Status
        self.is_r_pressed = False

        # Initialize temp-param
        self.last_status = None
        self.last_text = None
        self.last_emotion = None
        self.last_volume = None

        # Initialize keyord listener
        self.keyword_listener = None

    def set_callbacks(self,
                      press_callback: Optional[Callable] = None,
                      release_callback: Optional[Callable] = None,
                      status_callback: Optional[Callable] = None,
                      text_callback: Optional[Callable] = None,
                      emotion_callback: Optional[Callable] = None,
                      mode_callback: Optional[Callable] = None,
                      auto_callback: Optional[Callable] = None,
                      abort_callback: Optional[Callable] = None):
        """设置回调函数"""
        self.status_callback = status_callback
        self.text_callback = text_callback
        self.emotion_callback = emotion_callback
        self.auto_callback = auto_callback
        self.abort_callback = abort_callback

    def update_status(self, status: str):
        """更新状态文本"""
        if status != self.current_status:
            self.current_status = status
            self._print_current_status()

    def update_text(self, text: str):
        """更新TTS文本"""
        if text != self.current_text:
            self.current_text = text
            self._print_current_status()

    def update_emotion(self, emotion: str):
        """更新表情"""
        if emotion != self.current_emotion:
            self.current_emotion = emotion
            self._print_current_status()     

    def start_keyboard_listener(self):

        pass

    def stop_keyboard_listener(self):

        pass

    def update_button_status(self):

        pass

    def func_auto_run(self):

        """ Enable Auto Callback when Function Call"""

        try:

            if self.auto_callback:

                self.auto_callback()

        except Exception as e:

            self.logger.error(f"Funcation Call Fail: {e}")               

    def start(self):

        """启动CLI显示"""
        self._print_help()
        
        # 启动状态更新线程
        self.start_update_threads()

        # Start the Chating Function util Keyboard Interrupt
        self.func_auto_run()

        # 主循环
        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.on_close()

    def on_close(self):
        """关闭CLI显示"""
        self.running = False
        print("\n正在关闭应用...")
        #self.stop_keyboard_listener()

    def _print_help(self):
        """打印帮助信息"""
        print("\n=== 小智Ai命令行控制 ===")
        print("可用命令：")
        print("  r     - 开始/停止对话")
        print("  x     - 打断当前对话")
        print("  s     - 显示当前状态")
        print("  v 数字 - 设置音量(0-100)")
        print("  q     - 退出程序")
        print("  h     - 显示此帮助信息")
        print("=====================\n")

    def start_update_threads(self):
        """启动更新线程"""
        def update_loop():
            while self.running:
                try:
                    # 更新状态
                    if self.status_callback:
                        status = self.status_callback()
                        if status and status != self.current_status:
                            self.update_status(status)

                    # 更新文本
                    if self.text_callback:
                        text = self.text_callback()
                        if text and text != self.current_text:
                            self.update_text(text)

                    # 更新表情
                    if self.emotion_callback:
                        emotion = self.emotion_callback()
                        if emotion and emotion != self.current_emotion:
                            self.update_emotion(emotion)

                except Exception as e:
                    logger.error(f"状态更新错误: {e}")
                time.sleep(0.1)

        # 启动更新线程
        threading.Thread(target=update_loop, daemon=True).start()

    def _print_current_status(self):
        """打印当前状态"""
        # 检查是否有状态变化
        status_changed = (
            self.current_status != self.last_status or
            self.current_text != self.last_text or
            self.current_emotion != self.last_emotion or
            self.current_volume != self.last_volume
        )
        
        if status_changed:
            print("\n=== 当前状态 ===")
            print(f"状态: {self.current_status}")
            print(f"文本: {self.current_text}")
            print(f"表情: {self.current_emotion}")
            print(f"音量: {self.current_volume}%")
            print("===============\n")
            
            # 更新缓存
            self.last_status = self.current_status
            self.last_text = self.current_text
            self.last_emotion = self.current_emotion
            self.last_volume = self.current_volume