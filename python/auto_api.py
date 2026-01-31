import importlib
import sys

class AutoAPI:
    def __init__(self):
        # Map NL function names to (module, function)
        self.mapping = {
            # Chinese
            '截图': ('pyautogui', 'screenshot'),
            '点击': ('pyautogui', 'click'),
            '移动': ('pyautogui', 'moveTo'),
            '等待': ('time', 'sleep'),
            '输入': ('pyautogui', 'write'),
            '按键': ('pyautogui', 'press'),
            '获取窗口': ('pygetwindow', 'getWindowsWithTitle'),
            
            # English
            'screenshot': ('pyautogui', 'screenshot'),
            'click': ('pyautogui', 'click'),
            'move': ('pyautogui', 'moveTo'),
            'wait': ('time', 'sleep'),
            'type': ('pyautogui', 'write'),
            'press': ('pyautogui', 'press'),
            'get_window': ('pygetwindow', 'getWindowsWithTitle'),
        }

    def execute(self, func_name, args):
        if func_name not in self.mapping:
            raise ValueError(f"Unknown automation function: {func_name}")
        
        module_name, method_name = self.mapping[func_name]
        
        try:
            module = importlib.import_module(module_name)
            method = getattr(module, method_name)
            # Handle args - basic unpacking
            return method(*args)
        except ImportError as e:
            print(f"System: Module '{module_name}' import failed: {e}. Skipping execution of '{func_name}'.")
            return None
        except Exception as e:
            print(f"Runtime Error in '{func_name}': {e}")
            return None
