# NovoLang (New Multilingual Programming Language)

<div align="center">
  <img src="https://via.placeholder.com/150?text=NovoLang" alt="NovoLang Logo" width="120" height="120">
  <h1>NovoLang</h1>
  <p>
    <b>Programming without Language Barriers.</b>
  </p>
  <p>
    <a href="#features">Features</a> •
    <a href="#installation">Installation</a> •
    <a href="#usage">Usage</a> •
    <a href="#documentation">Documentation</a> •
    <a href="#license">License</a>
  </p>
</div>

---

**NovoLang** is a next-generation programming language designed to support keywords in multiple languages natively. Whether you speak English, Chinese, Japanese, Korean, or Russian, NovoLang understands you. It comes with built-in automation capabilities and a powerful, lightweight IDE.

## ✨ Features

- **🌏 Native Multilingual Support**: Write code using keywords in **English, Chinese (Simplified), Japanese, Korean, or Russian**.
- **🤖 Built-in Automation**: First-class support for GUI automation (click, type, screenshot, etc.) without external libraries.
- **⚡ Easy to Learn**: Python-like syntax that reads like natural language.
- **🛠️ Integrated IDE**: Comes with a dedicated editor featuring syntax highlighting, auto-completion, and one-click execution.
- **📦 Single Executable**: The entire environment (Compiler + IDE) is packed into a single portable EXE.

## 🚀 Installation

### Option 1: Download Pre-built Binary
Download the latest `NovoLangEditor.exe` from the [Releases](https://github.com/NovoLang/releases) page (coming soon).

### Option 2: Build from Source
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/NovoLang.git
   cd NovoLang
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the IDE:
   ```bash
   python editor.py
   ```
4. (Optional) Build EXE:
   ```bash
   python -m PyInstaller --onefile --windowed --hidden-import=pyautogui --hidden-import=pygetwindow editor.py
   ```

## 📖 Usage

### Writing Your First Script

Open NovoLang IDE and type the following (in English or your preferred language):

**English:**
```python
function main() {
    print("Hello, World!")
    run("notepad.exe")
    wait(2)
    type("Automating with NovoLang is easy!")
}
```

**Chinese:**
```python
函数 主程序() {
    打印("你好，世界！")
    运行("notepad.exe")
    等待(2)
    输入("使用 NovoLang 自动化非常简单！")
}
```

### Automation Commands

| Command (English) | Command (Chinese) | Description |
|-------------------|-------------------|-------------|
| `click(x, y)` | `点击(x, y)` | Click at coordinates (optional) |
| `type("text")` | `输入("文本")` | Type text string |
| `screenshot("f.png")`| `截图("文件名")` | Take a screenshot |
| `run("app")` | `运行("程序")` | Launch an application |
| `wait(seconds)` | `等待(秒数)` | Pause execution |

## 🏗️ Project Structure

- `python/`: Core language implementation (Lexer, Parser, Executor).
- `c++/`: High-performance backend modules (optional).
- `editor.py`: The main IDE entry point (Tkinter-based).
- `index.html`: Official homepage.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
