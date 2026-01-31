import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sys
import io
import os
import threading
import re

# Import NovoLang core
sys.path.append(os.path.join(os.path.dirname(__file__), 'python'))

try:
    from lexer import Lexer
    from parser import Parser
    from py_executor import PyExecutor
    try:
        import novolang_core
        HAS_CPP = True
    except ImportError:
        HAS_CPP = False
except ImportError as e:
    # Fallback for UI testing if core not found
    print(f"Core import error: {e}")
    HAS_CPP = False

class RedirectText(io.StringIO):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def write(self, string):
        self.text_widget.configure(state='normal')
        self.text_widget.insert('end', string)
        self.text_widget.see('end')
        self.text_widget.configure(state='disabled')

    def flush(self):
        pass

class LineNumberCanvas(tk.Canvas):
    def __init__(self, *args, **kwargs):
        tk.Canvas.__init__(self, *args, **kwargs)
        self.text_widget = None

    def attach(self, text_widget):
        self.text_widget = text_widget

    def redraw(self, *args):
        '''Redraw line numbers'''
        self.delete("all")

        i = self.text_widget.index("@0,0")
        while True :
            dline= self.text_widget.dlineinfo(i)
            if dline is None: break
            y = dline[1]
            linenum = str(i).split(".")[0]
            self.create_text(2, y, anchor="nw", text=linenum, fill="#666666", font=("Consolas", 10))
            i = self.text_widget.index("%s+1line" % i)

class CodeEditor(tk.Frame):
    def __init__(self, parent, file_path=None):
        super().__init__(parent)
        self.file_path = file_path
        self.is_modified = False

        # Scrollbar
        self.scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Text Area
        self.text_area = tk.Text(self, wrap=tk.NONE, undo=True, font=("Consolas", 12),
                                yscrollcommand=self.scrollbar.set)
        self.text_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.text_area.yview)

        # Line Numbers
        self.linenumbers = LineNumberCanvas(self, width=40, bg="#f0f0f0", highlightthickness=0)
        self.linenumbers.pack(side=tk.LEFT, fill=tk.Y)
        self.linenumbers.attach(self.text_area)

        # Bind events
        self.text_area.bind("<KeyRelease>", self._on_change)
        self.text_area.bind("<MouseWheel>", self._on_scroll)
        self.text_area.bind("<Button-1>", self._on_click)
        self.text_area.bind("<Configure>", self._on_scroll)
        
        # Syntax Highlighting Tags
        self._setup_tags()
        
        if file_path:
            self.load_file(file_path)

    def _setup_tags(self):
        # Dev-C++ Style Colors
        self.text_area.tag_configure("KEYWORD", foreground="#0000FF", font=("Consolas", 12, "bold")) # Blue
        self.text_area.tag_configure("STRING", foreground="#A00000") # Dark Red (String) - Dev-C++ uses blue/red usually
        self.text_area.tag_configure("COMMENT", foreground="#008000", font=("Consolas", 12, "italic")) # Green
        self.text_area.tag_configure("NUMBER", foreground="#800080") # Purple
        self.text_area.tag_configure("FUNCTION", foreground="#000000", font=("Consolas", 12, "bold")) 

    def highlight_syntax(self):
        content = self.text_area.get("1.0", tk.END)
        
        # Clear existing tags
        for tag in ["KEYWORD", "STRING", "COMMENT", "NUMBER", "FUNCTION"]:
            self.text_area.tag_remove(tag, "1.0", tk.END)

        # Keywords
        keywords = [
            # Chinese
            "如果", "否则", "循环", "打印", "定义", "返回", "当", "自动", "真", "假", "空",
            # English
            "if", "else", "loop", "for", "print", "def", "var", "return", "while", "auto", "true", "false", "null",
            # Japanese
            "もし", "その他", "繰り返し", "表示", "定義", "戻る", "間", "自動", "真", "偽", "無",
            # Korean
            "만약", "아니면", "반복", "출력", "정의", "반환", "동안", "참", "거짓", "비어",
            # Russian
            "если", "иначе", "цикл", "печать", "определить", "вернуть", "пока", "авто", "истина", "ложь", "ноль"
        ]
        for kw in keywords:
            start = "1.0"
            while True:
                pos = self.text_area.search(kw, start, stopindex=tk.END)
                if not pos: break
                end = f"{pos}+{len(kw)}c"
                self.text_area.tag_add("KEYWORD", pos, end)
                start = end

        # Strings
        start = "1.0"
        while True:
            # Simple regex for strings
            pos = self.text_area.search(r'"[^"]*"', start, stopindex=tk.END, regexp=True)
            if not pos: break
            # Calculate length match
            match_len = 0
            # Tkinter search doesn't return match length easily with regex, 
            # so we might need to verify or use a different approach.
            # Simplified: Find next quote
            end_quote = self.text_area.search('"', f"{pos}+1c", stopindex=tk.END)
            if end_quote:
                end = f"{end_quote}+1c"
                self.text_area.tag_add("STRING", pos, end)
                start = end
            else:
                break

        # Comments
        start = "1.0"
        while True:
            pos = self.text_area.search(r'//.*', start, stopindex=tk.END, regexp=True)
            if not pos: break
            # Find end of line
            line_end = self.text_area.index(f"{pos} lineend")
            self.text_area.tag_add("COMMENT", pos, line_end)
            start = f"{pos}+1line"

        # Numbers
        start = "1.0"
        while True:
            pos = self.text_area.search(r'\d+', start, stopindex=tk.END, regexp=True)
            if not pos: break
            
            # Hacky length check
            # Real impl would do full regex scan of content and map indices
            # Here we just highlight single digit sequences
            # To fix length, we can check char by char
            count = 0
            while True:
                char = self.text_area.get(f"{pos}+{count}c")
                if char.isdigit() or char == '.':
                    count += 1
                else:
                    break
            
            end = f"{pos}+{count}c"
            self.text_area.tag_add("NUMBER", pos, end)
            start = end

    def _on_change(self, event=None):
        self.linenumbers.redraw()
        self.highlight_syntax()
        self.is_modified = True

    def _on_scroll(self, event=None):
        self.linenumbers.redraw()
        # Pass scroll to text
        # self.text_area.yview_scroll(...) handled by binding default?
        # Actually MouseWheel on canvas might need to propagate
        
    def _on_click(self, event=None):
        self.linenumbers.redraw()

    def load_file(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.text_area.delete("1.0", tk.END)
                self.text_area.insert("1.0", content)
                self._on_change()
                self.is_modified = False
                self.file_path = path
        except Exception as e:
            messagebox.showerror("Error", f"Could not read file: {e}")

    def save_file(self):
        if not self.file_path:
            return self.save_as()
        
        try:
            content = self.text_area.get("1.0", tk.END)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(content) # Text widget adds a newline at end usually
            self.is_modified = False
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file: {e}")
            return False

    def save_as(self):
        path = filedialog.asksaveasfilename(defaultextension=".nl", filetypes=[("NovoLang Files", "*.nl"), ("All Files", "*.*")])
        if path:
            self.file_path = path
            return self.save_file()
        return False

TRANSLATIONS = {
    "zh": {
        "file": "文件(F)", "new": "新建", "open": "打开", "save": "保存", "exit": "退出",
        "run_menu": "运行(E)", "run": "编译运行", "view": "视图(V)", "clear": "清空输出",
        "tools": "工具(T)", "shortcut": "创建桌面快捷方式",
        "help": "帮助(H)", "tutorial": "新手教程", "about": "关于", "lang": "语言(L)",
        "project": "项目资源管理器", "output": "编译/运行输出", "ready": "就绪",
        "untitled": "未命名", "opened": "已打开", "saved": "已保存",
        "shortcut_success": "快捷方式已创建到桌面！", "shortcut_fail": "创建快捷方式失败: ",
        "assoc": "注册 .nl 文件关联", "assoc_success": ".nl 文件已成功关联到编辑器！", "assoc_fail": "文件关联失败: "
    },
    "en": {
        "file": "File(F)", "new": "New", "open": "Open", "save": "Save", "exit": "Exit",
        "run_menu": "Run(E)", "run": "Compile & Run", "view": "View(V)", "clear": "Clear Output",
        "tools": "Tools(T)", "shortcut": "Create Desktop Shortcut",
        "help": "Help(H)", "tutorial": "Tutorial", "about": "About", "lang": "Language(L)",
        "project": "Project Explorer", "output": "Output", "ready": "Ready",
        "untitled": "Untitled", "opened": "Opened", "saved": "Saved",
        "shortcut_success": "Shortcut created on Desktop!", "shortcut_fail": "Failed to create shortcut: ",
        "assoc": "Register .nl File Association", "assoc_success": ".nl files associated successfully!", "assoc_fail": "Association failed: "
    },
    "ja": {
        "file": "ファイル(F)", "new": "新規作成", "open": "開く", "save": "保存", "exit": "終了",
        "run_menu": "実行(E)", "run": "コンパイルと実行", "view": "表示(V)", "clear": "出力をクリア",
        "tools": "ツール(T)", "shortcut": "デスクトップにショートカットを作成",
        "help": "ヘルプ(H)", "tutorial": "チュートリアル", "about": "バージョン情報", "lang": "言語(L)",
        "project": "プロジェクト", "output": "出力", "ready": "準備完了",
        "untitled": "無題", "opened": "開きました", "saved": "保存しました",
        "shortcut_success": "デスクトップにショートカットを作成しました！", "shortcut_fail": "ショートカットの作成に失敗しました: ",
        "assoc": ".nlファイルの関連付け", "assoc_success": ".nlファイルが関連付けられました！", "assoc_fail": "関連付けに失敗しました: "
    },
    "ko": {
        "file": "파일(F)", "new": "새로 만들기", "open": "열기", "save": "저장", "exit": "종료",
        "run_menu": "실행(E)", "run": "컴파일 및 실행", "view": "보기(V)", "clear": "출력 지우기",
        "tools": "도구(T)", "shortcut": "바탕 화면 바로 가기 만들기",
        "help": "도움말(H)", "tutorial": "튜토리얼", "about": "정보", "lang": "언어(L)",
        "project": "프로젝트 탐색기", "output": "출력", "ready": "준비됨",
        "untitled": "무제", "opened": "열림", "saved": "저장됨",
        "shortcut_success": "바탕 화면에 바로 가기를 만들었습니다!", "shortcut_fail": "바로 가기 만들기 실패: ",
        "assoc": ".nl 파일 연결 등록", "assoc_success": ".nl 파일이 성공적으로 연결되었습니다!", "assoc_fail": "연결 실패: "
    },
    "ru": {
        "file": "Файл(F)", "new": "Новый", "open": "Открыть", "save": "Сохранить", "exit": "Выход",
        "run_menu": "Запуск(E)", "run": "Компилировать и запустить", "view": "Вид(V)", "clear": "Очистить вывод",
        "tools": "Инструменты(T)", "shortcut": "Создать ярлык на рабочем столе",
        "help": "Справка(H)", "tutorial": "Учебник", "about": "О программе", "lang": "Язык(L)",
        "project": "Проводник проекта", "output": "Вывод", "ready": "Готов",
        "untitled": "Безымянный", "opened": "Открыто", "saved": "Сохранено",
        "shortcut_success": "Ярлык создан на рабочем столе!", "shortcut_fail": "Не удалось создать ярлык: ",
        "assoc": "Связать файлы .nl", "assoc_success": "Файлы .nl успешно связаны!", "assoc_fail": "Ошибка связи: "
    }
}

TUTORIALS = {
    "zh": """// NovoLang 新手教程
// 这是一个注释

定义 a = 10
如果 (a > 5) {
    打印("你好，NovoLang！")
    打印("a 的值是: " + a)
}

循环 (i = 0; i < 3; i = i + 1) {
    打印("计数: " + i)
}
""",
    "en": """// NovoLang Tutorial
// This is a comment

var a = 10
if (a > 5) {
    print("Hello, NovoLang!")
    print("Value of a is: " + a)
}

for (i = 0; i < 3; i = i + 1) {
    print("Count: " + i)
}
""",
    "ja": """// NovoLang チュートリアル
// コメントです

定義 a = 10
もし (a > 5) {
    表示("こんにちは、NovoLang！")
    表示("a の値: " + a)
}

繰り返し (i = 0; i < 3; i = i + 1) {
    表示("カウント: " + i)
}
""",
    "ko": """// NovoLang 튜토리얼
// 주석입니다

정의 a = 10
만약 (a > 5) {
    출력("안녕하세요, NovoLang!")
    출력("a 값: " + a)
}

반복 (i = 0; i < 3; i = i + 1) {
    출력("카운트: " + i)
}
""",
    "ru": """// Учебник NovoLang
// Это комментарий

определить a = 10
если (a > 5) {
    печать("Привет, NovoLang!")
    печать("Значение a: " + a)
}

цикл (i = 0; i < 3; i = i + 1) {
    печать("Счет: " + i)
}
"""
}

import subprocess
import winreg

class IDE(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Dev-NovoLang IDE")
        self.geometry("1200x800")
        
        self.current_lang = "zh"
        
        # Set theme
        style = ttk.Style()
        style.theme_use('clam') 
        
        # Icons
        self.icons = {
            "new": "📄", "open": "📂", "save": "💾", "run": "▶", "compile": "🔨"
        }

        self.sidebar_label = None
        self.output_frame = None
        self.toolbar = None
        
        self.create_main_layout()
        self.create_statusbar()
        self.refresh_ui()
        
        # Bind shortcuts
        self.bind("<Control-n>", lambda e: self.new_file())
        self.bind("<Control-o>", lambda e: self.open_file())
        self.bind("<Control-s>", lambda e: self.save_current_file())
        self.bind("<F9>", lambda e: self.run_code())

        # Load file tree
        self.refresh_file_tree(os.getcwd())

        # Open file from command line args
        if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
            self.load_file_in_new_tab(sys.argv[1])

    def load_file_in_new_tab(self, path):
        """Helper to load a file in a new tab"""
        # Check if already open
        for tab_id in self.notebook.tabs():
            widget = self.notebook.nametowidget(tab_id)
            if widget.file_path == path:
                self.notebook.select(widget)
                return

        editor = CodeEditor(self.notebook, file_path=path)
        filename = os.path.basename(path)
        self.notebook.add(editor, text=filename)
        self.notebook.select(editor)
        self.statusbar.config(text=f"{self.tr('opened')} {path}")

    def tr(self, key):
        return TRANSLATIONS.get(self.current_lang, TRANSLATIONS["zh"]).get(key, key)

    def refresh_ui(self):
        self.create_menu()
        if self.toolbar: self.toolbar.destroy()
        self.create_toolbar()
        
        if self.sidebar_label: self.sidebar_label.config(text=self.tr("project"))
        if self.output_frame: self.output_frame.config(text=self.tr("output"))
        self.statusbar.config(text=self.tr("ready"))

    def change_language(self, lang):
        self.current_lang = lang
        self.refresh_ui()

    def create_shortcut(self):
        try:
            # Determine path to exe
            if getattr(sys, 'frozen', False):
                target_path = sys.executable
                working_dir = os.path.dirname(sys.executable)
            else:
                target_path = os.path.abspath(__file__)
                working_dir = os.path.dirname(os.path.abspath(__file__))

            # Get Desktop path via environment variable
            desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
            shortcut_path = os.path.join(desktop, "NovoLang IDE.lnk")

            # PowerShell command to create shortcut
            ps_script = f"$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('{shortcut_path}'); $s.TargetPath = '{target_path}'; $s.WorkingDirectory = '{working_dir}'; $s.Save()"
            
            subprocess.run(["powershell", "-Command", ps_script], check=True, shell=True)
            
            messagebox.showinfo(self.tr("tools"), self.tr("shortcut_success"))
        except Exception as e:
            messagebox.showerror(self.tr("tools"), f"{self.tr('shortcut_fail')}{e}")

    def register_association(self):
        try:
            # Determine path to exe
            if getattr(sys, 'frozen', False):
                target_path = sys.executable
            else:
                target_path = sys.executable # When running as script, this registers python.exe which is not ideal but okay for dev
                # Better: only allow in frozen mode or warn
                if not sys.executable.endswith("NovoLangEditor.exe"):
                     target_path = os.path.abspath(__file__) # This won't work directly without python invoker
                     # For dev mode, maybe skip or just warn
            
            # Use HKCU to avoid admin requirement
            key_path = r"Software\Classes\.nl"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                winreg.SetValue(key, "", winreg.REG_SZ, "NovoLangSource")

            key_path = r"Software\Classes\NovoLangSource"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                winreg.SetValue(key, "", winreg.REG_SZ, "NovoLang Source File")
            
            # Icon
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path + r"\DefaultIcon") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, f'"{target_path}",0')
            
            # Command
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path + r"\shell\open\command") as key:
                if getattr(sys, 'frozen', False):
                    cmd = f'"{target_path}" "%1"'
                else:
                    # If running from source, assume python launch
                    # Note: This is tricky for double click. 
                    # Ideally we only support this fully in compiled EXE.
                    python_exe = sys.executable
                    script = os.path.abspath(__file__)
                    # Escape paths?
                    cmd = f'"{python_exe}" "{script}" "%1"'
                
                winreg.SetValue(key, "", winreg.REG_SZ, cmd)
                
            # Notify explorer of change (optional, but good)
            try:
                import ctypes
                ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, 0, 0) # SHCNE_ASSOCCHANGED
            except:
                pass

            messagebox.showinfo(self.tr("tools"), self.tr("assoc_success"))
        except Exception as e:
            messagebox.showerror(self.tr("tools"), f"{self.tr('assoc_fail')}{e}")

    def create_menu(self):
        menu_bar = tk.Menu(self)
        self.config(menu=menu_bar)

        # File Menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label=self.tr("file"), menu=file_menu)
        file_menu.add_command(label=self.tr("new"), accelerator="Ctrl+N", command=self.new_file)
        file_menu.add_command(label=self.tr("open"), accelerator="Ctrl+O", command=self.open_file)
        file_menu.add_command(label=self.tr("save"), accelerator="Ctrl+S", command=self.save_current_file)
        file_menu.add_separator()
        file_menu.add_command(label=self.tr("exit"), command=self.quit)

        # Execute Menu
        exec_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label=self.tr("run_menu"), menu=exec_menu)
        exec_menu.add_command(label=self.tr("run"), accelerator="F9", command=self.run_code)
        
        # View Menu
        view_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label=self.tr("view"), menu=view_menu)
        view_menu.add_command(label=self.tr("clear"), command=self.clear_output)

        # Tools Menu
        tools_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label=self.tr("tools"), menu=tools_menu)
        tools_menu.add_command(label=self.tr("shortcut"), command=self.create_shortcut)
        tools_menu.add_command(label=self.tr("assoc"), command=self.register_association)

        # Language Menu
        lang_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label=self.tr("lang"), menu=lang_menu)
        lang_menu.add_command(label="中文 (Chinese)", command=lambda: self.change_language("zh"))
        lang_menu.add_command(label="English", command=lambda: self.change_language("en"))
        lang_menu.add_command(label="日本語 (Japanese)", command=lambda: self.change_language("ja"))
        lang_menu.add_command(label="한국어 (Korean)", command=lambda: self.change_language("ko"))
        lang_menu.add_command(label="Русский (Russian)", command=lambda: self.change_language("ru"))

        # Help Menu
        help_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label=self.tr("help"), menu=help_menu)
        help_menu.add_command(label=self.tr("tutorial"), command=self.open_tutorial)
        help_menu.add_command(label=self.tr("about"), command=self.show_about)

    def show_about(self):
        story = (
            "NovoLang IDE v1.0\n\n"
            "【开发者故事 / Developer Story】\n\n"
            "NovoLang 的诞生源于一个简单的愿景：让编程不再受限于母语。\n"
            "编程应当是逻辑的艺术，而非语言的障碍。\n\n"
            "我们致力于打造一个真正支持多语言（中/英/日/韩/俄）的编程环境，"
            "让初学者能够用自己最熟悉的语言，写下第一行代码，开启创造之旅。\n\n"
            "NovoLang was born from a vision: to make coding accessible to everyone.\n"
            "We believe programming should be about logic, not language barriers.\n\n"
            "Powered by Python & C++.\n"
            "Developed with ❤️ by The NovoLang Team."
        )
        messagebox.showinfo(self.tr("about"), story)

    def create_toolbar(self):
        self.toolbar = ttk.Frame(self)
        self.toolbar.pack(side=tk.TOP, fill=tk.X, before=self.main_paned)

        def add_btn(text, cmd):
            btn = ttk.Button(self.toolbar, text=text, width=4, command=cmd)
            btn.pack(side=tk.LEFT, padx=2, pady=2)
            
        add_btn(self.icons["new"], self.new_file)
        add_btn(self.icons["open"], self.open_file)
        add_btn(self.icons["save"], self.save_current_file)
        ttk.Separator(self.toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        add_btn(self.icons["run"], self.run_code)

    def create_main_layout(self):
        self.main_paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        self.main_paned.pack(fill=tk.BOTH, expand=True)

        # Left Sidebar
        sidebar_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(sidebar_frame, width=200)
        
        self.sidebar_label = ttk.Label(sidebar_frame, text="Project", font=("Arial", 9, "bold"))
        self.sidebar_label.pack(side=tk.TOP, fill=tk.X)
        
        self.file_tree = ttk.Treeview(sidebar_frame)
        self.file_tree.pack(fill=tk.BOTH, expand=True)
        self.file_tree.heading("#0", text="Files", anchor=tk.W)
        self.file_tree.bind("<Double-1>", self.on_tree_double_click)

        # Right Content
        self.right_paned = tk.PanedWindow(self.main_paned, orient=tk.VERTICAL, sashrelief=tk.RAISED)
        self.main_paned.add(self.right_paned)

        # Notebook
        self.notebook = ttk.Notebook(self.right_paned)
        self.right_paned.add(self.notebook, height=500)

        # Output
        self.output_frame = ttk.LabelFrame(self.right_paned, text="Output")
        self.right_paned.add(self.output_frame)
        
        self.output_text = tk.Text(self.output_frame, height=10, bg="white", font=("Consolas", 10))
        self.output_text.pack(fill=tk.BOTH, expand=True)
        self.output_text.configure(state='disabled')

    def create_statusbar(self):
        self.statusbar = ttk.Label(self, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)

    def open_tutorial(self):
        content = TUTORIALS.get(self.current_lang, TUTORIALS["zh"])
        editor = CodeEditor(self.notebook)
        editor.text_area.insert("1.0", content)
        editor.highlight_syntax()
        self.notebook.add(editor, text=self.tr("tutorial"))
        self.notebook.select(editor)

    def refresh_file_tree(self, path):
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        root_node = self.file_tree.insert("", "end", text=path, open=True)
        
        try:
            for item in os.listdir(path):
                full_path = os.path.join(path, item)
                if os.path.isdir(full_path):
                    self.file_tree.insert(root_node, "end", text=item, open=False)
                elif item.endswith(".nl"):
                    self.file_tree.insert(root_node, "end", text=item, values=[full_path])
        except Exception as e:
            print(e)

    def on_tree_double_click(self, event):
        item_id = self.file_tree.selection()[0]
        item_text = self.file_tree.item(item_id, "text")
        
        if item_text.endswith(".nl"):
            cwd = os.getcwd()
            full_path = os.path.join(cwd, item_text)
            if os.path.exists(full_path):
                self.open_file_by_path(full_path)

    def new_file(self):
        editor = CodeEditor(self.notebook)
        self.notebook.add(editor, text=self.tr("untitled"))
        self.notebook.select(editor)

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("NovoLang Files", "*.nl"), ("All Files", "*.*")])
        if path:
            self.open_file_by_path(path)

    def open_file_by_path(self, path):
        for tab in self.notebook.tabs():
            widget = self.notebook.nametowidget(tab)
            if isinstance(widget, CodeEditor) and widget.file_path == path:
                self.notebook.select(widget)
                return

        editor = CodeEditor(self.notebook, file_path=path)
        self.notebook.add(editor, text=os.path.basename(path))
        self.notebook.select(editor)
        self.statusbar.config(text=f"{self.tr('opened')} {path}")

    def save_current_file(self):
        current = self.get_current_editor()
        if current:
            if current.save_file():
                self.notebook.tab(current, text=os.path.basename(current.file_path))
                self.statusbar.config(text=f"{self.tr('saved')} {current.file_path}")

    def get_current_editor(self):
        select = self.notebook.select()
        if select:
            return self.notebook.nametowidget(select)
        return None

    def clear_output(self):
        self.output_text.configure(state='normal')
        self.output_text.delete(1.0, tk.END)
        self.output_text.configure(state='disabled')

    def run_code(self):
        editor = self.get_current_editor()
        if not editor:
            return

        code = editor.text_area.get("1.0", tk.END)
        if not code.strip():
            return
        
        self.clear_output()
        self.output_text.configure(state='normal')
        self.output_text.insert(tk.END, f"--------------------Configuration: NovoLang - Debug--------------------\n")
        self.output_text.configure(state='disabled')

        threading.Thread(target=self._execute_logic, args=(code,), daemon=True).start()

    def _execute_logic(self, code):
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        
        redirector = RedirectText(self.output_text)
        sys.stdout = redirector
        sys.stderr = redirector

        try:
            lexer = Lexer(code)
            tokens = lexer.tokenize()
            
            parser = Parser(tokens)
            ast = parser.parse()

            if HAS_CPP:
                print("Compiling with C++ Engine...")
                executor = novolang_core.ASTExecutor()
                executor.execute(ast)
            else:
                print("Compiling with Python Engine (Legacy)...")
                executor = PyExecutor()
                executor.execute(ast)
            
            print("\n--------------------------------")
            print("Process exited with return value 0")
            print("Press any key to continue . . .") 
                
        except Exception as e:
            print(f"\n[Error] {e}")
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

if __name__ == "__main__":
    app = IDE()
    app.mainloop()
