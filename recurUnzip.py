import os
import time
import zipfile
import tarfile
import shutil
import tempfile
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter import ttk
from tkinter import font

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES

    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

SUPPORTED_EXTS = (".tar.gz", ".tgz", ".tar", ".zip")


# ---------------- 解压核心逻辑 ----------------
def get_archive_name(filename):
    for ext in SUPPORTED_EXTS:
        if filename.lower().endswith(ext):
            return filename[:-len(ext)]
    return None


def safe_zip_extract(zip_path, extract_dir):
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for info in zf.infolist():
            try:
                name = info.filename.encode('cp437').decode('gbk')
            except Exception:
                name = info.filename

            target = os.path.join(extract_dir, name)

            if info.is_dir():
                os.makedirs(target, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(target), exist_ok=True)

                with zf.open(info) as src, open(target, 'wb') as dst:
                    shutil.copyfileobj(src, dst)

                date_time = info.date_time
                mtime = time.mktime(date_time + (0, 0, -1))
                os.utime(target, (mtime, mtime))


def extract_archive(archive_path, log, delete_after):
    base_dir = os.path.dirname(archive_path)
    filename = os.path.basename(archive_path)

    name = get_archive_name(filename)
    if not name:
        return False

    target_dir = os.path.join(base_dir, name)
    if os.path.exists(target_dir):
        return False

    try:
        os.makedirs(target_dir, exist_ok=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            if filename.lower().endswith(".zip"):
                safe_zip_extract(archive_path, tmpdir)
            else:
                with tarfile.open(archive_path, "r:*") as tf:
                    tf.extractall(tmpdir)

            items = os.listdir(tmpdir)
            src_dir = os.path.join(tmpdir, items[0]) if len(items) == 1 and os.path.isdir(
                os.path.join(tmpdir, items[0])) else tmpdir

            for item in os.listdir(src_dir):
                shutil.move(os.path.join(src_dir, item), os.path.join(target_dir, item))

        if delete_after:
            os.remove(archive_path)
            log(f"✅ 解压并删除：{archive_path}", "success")
        else:
            log(f"✅ 解压完成：{archive_path}", "success")

        return True

    except Exception as e:
        log(f"❌ 解压失败：{archive_path}", "error")
        log(f"    原因：{str(e)[:100]}...", "info")
        if os.path.exists(target_dir) and not os.listdir(target_dir):
            shutil.rmtree(target_dir, ignore_errors=True)
        return False


def recursive_extract(root_path, log, delete_after):
    while True:
        extracted = False
        all_files = []
        for root, _, files in os.walk(root_path):
            for f in files:
                all_files.append(os.path.join(root, f))

        for f in all_files:
            if extract_archive(f, log, delete_after):
                extracted = True

        if not extracted:
            break

    log("🎉 全部解压完成！", "success")


# ---------------- 美化版 GUI ----------------
class ModernApp(TkinterDnD.Tk if DND_AVAILABLE else tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("智能解压工具 | Smart Archive Extractor")
        self.geometry("1000x650")
        self.minsize(900, 550)

        # 设置应用图标（如果有的话）
        try:
            self.iconbitmap(default='')  # 可以在这里指定图标文件路径
        except:
            pass

        # 颜色方案 - 现代深色主题
        self.colors = {
            "bg_primary": "#1a1a2e",
            "bg_secondary": "#16213e",
            "bg_tertiary": "#0f3460",
            "accent_blue": "#3498db",
            "accent_green": "#2ecc71",
            "accent_red": "#e74c3c",
            "accent_orange": "#e67e22",
            "text_primary": "#ecf0f1",
            "text_secondary": "#bdc3c7",
            "border": "#2c3e50",
            "success": "#27ae60",
            "warning": "#f39c12",
            "error": "#c0392b"
        }

        self.configure(bg=self.colors["bg_primary"])

        # 自定义字体
        self.fonts = {
            "title": ("Microsoft YaHei UI", 16, "bold"),
            "subtitle": ("Microsoft YaHei UI", 11),
            "normal": ("Microsoft YaHei UI", 10),
            "mono": ("Consolas", 10),
            "button": ("Microsoft YaHei UI", 10, "bold")
        }

        self.path_var = tk.StringVar()
        self.delete_var = tk.BooleanVar(value=False)
        self.running = False

        self.create_custom_styles()
        self.create_widgets()

        if DND_AVAILABLE:
            self.enable_drag()

    def create_custom_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        # 配置主框架样式
        style.configure("Primary.TFrame", background=self.colors["bg_primary"])
        style.configure("Secondary.TFrame", background=self.colors["bg_secondary"])
        style.configure("Tertiary.TFrame", background=self.colors["bg_tertiary"])

        # 按钮样式
        style.configure("Primary.TButton",
                        background=self.colors["accent_blue"],
                        foreground=self.colors["text_primary"],
                        borderwidth=0,
                        focusthickness=3,
                        focuscolor=self.colors["accent_blue"],
                        font=self.fonts["button"],
                        padding=10)
        style.map("Primary.TButton",
                  background=[('active', '#2980b9'), ('pressed', '#1f618d')])

        style.configure("Success.TButton",
                        background=self.colors["accent_green"],
                        foreground=self.colors["text_primary"],
                        borderwidth=0,
                        font=self.fonts["button"],
                        padding=10)
        style.map("Success.TButton",
                  background=[('active', '#27ae60'), ('pressed', '#219653')])

        style.configure("Secondary.TButton",
                        background=self.colors["bg_tertiary"],
                        foreground=self.colors["text_primary"],
                        borderwidth=1,
                        relief="solid",
                        font=self.fonts["button"],
                        padding=8)

        # 标签样式
        style.configure("Title.TLabel",
                        background=self.colors["bg_primary"],
                        foreground=self.colors["accent_blue"],
                        font=self.fonts["title"])

        style.configure("Subtitle.TLabel",
                        background=self.colors["bg_primary"],
                        foreground=self.colors["text_secondary"],
                        font=self.fonts["subtitle"])

        style.configure("Normal.TLabel",
                        background=self.colors["bg_primary"],
                        foreground=self.colors["text_primary"],
                        font=self.fonts["normal"])

        # 输入框样式
        style.configure("Modern.TEntry",
                        fieldbackground=self.colors["bg_tertiary"],
                        foreground=self.colors["text_primary"],
                        borderwidth=2,
                        relief="flat",
                        padding=8)

        # 复选框样式
        style.configure("Modern.TCheckbutton",
                        background=self.colors["bg_primary"],
                        foreground=self.colors["text_primary"],
                        font=self.fonts["normal"])

        # 进度条样式
        style.configure("Custom.Horizontal.TProgressbar",
                        background=self.colors["accent_blue"],
                        troughcolor=self.colors["bg_tertiary"],
                        borderwidth=0,
                        lightcolor=self.colors["accent_blue"],
                        darkcolor=self.colors["accent_blue"])

    def create_widgets(self):
        # 主容器
        main_container = ttk.Frame(self, style="Primary.TFrame")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # 标题区域
        title_frame = ttk.Frame(main_container, style="Primary.TFrame")
        title_frame.pack(fill="x", pady=(0, 20))

        ttk.Label(title_frame, text="📦 智能解压工具", style="Title.TLabel").pack(side="left")

        version_label = ttk.Label(title_frame, text="v2.0", style="Subtitle.TLabel")
        version_label.pack(side="right")

        # 拖拽区域（视觉上）
        drop_frame = ttk.Frame(main_container, style="Secondary.TFrame")
        drop_frame.pack(fill="x", pady=(0, 20))
        drop_frame.pack_propagate(False)
        drop_frame.configure(height=120)

        drop_label = tk.Label(drop_frame,
                              text="📤 拖拽文件或文件夹到这里",
                              bg=self.colors["bg_secondary"],
                              fg=self.colors["text_secondary"],
                              font=self.fonts["subtitle"],
                              pady=20)
        drop_label.pack(expand=True)

        drop_sublabel = tk.Label(drop_frame,
                                 text="支持格式: .zip .tar .tar.gz .tgz",
                                 bg=self.colors["bg_secondary"],
                                 fg=self.colors["accent_blue"],
                                 font=self.fonts["normal"])
        drop_sublabel.pack()

        # 路径选择区域
        path_frame = ttk.Frame(main_container, style="Primary.TFrame")
        path_frame.pack(fill="x", pady=(0, 20))

        ttk.Label(path_frame, text="当前路径：", style="Normal.TLabel").pack(anchor="w")

        # 输入框和按钮容器
        input_frame = ttk.Frame(path_frame, style="Primary.TFrame")
        input_frame.pack(fill="x", pady=(5, 0))

        self.path_entry = ttk.Entry(input_frame,
                                    textvariable=self.path_var,
                                    style="Modern.TEntry",
                                    font=self.fonts["normal"])
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        button_container = ttk.Frame(input_frame, style="Primary.TFrame")
        button_container.pack(side="right")

        ttk.Button(button_container,
                   text="📁 选择文件",
                   command=self.choose_file,
                   style="Secondary.TButton").pack(side="left", padx=(0, 5))

        ttk.Button(button_container,
                   text="📂 选择文件夹",
                   command=self.choose_dir,
                   style="Secondary.TButton").pack(side="left")

        # 选项区域
        options_frame = ttk.Frame(main_container, style="Primary.TFrame")
        options_frame.pack(fill="x", pady=(0, 20))

        self.delete_check = ttk.Checkbutton(options_frame,
                                            text="解压后删除原始压缩文件",
                                            variable=self.delete_var,
                                            style="Modern.TCheckbutton")
        self.delete_check.pack(side="left", padx=(0, 20))

        self.status_label = tk.Label(options_frame,
                                     text="就绪",
                                     bg=self.colors["bg_primary"],
                                     fg=self.colors["accent_green"],
                                     font=self.fonts["normal"])
        self.status_label.pack(side="left")

        # 进度条
        self.progress = ttk.Progressbar(main_container,
                                        mode="indeterminate",
                                        style="Custom.Horizontal.TProgressbar",
                                        length=100)
        self.progress.pack(fill="x", pady=(0, 15))

        # 开始按钮
        self.start_button = ttk.Button(main_container,
                                       text="🚀 开始解压",
                                       command=self.start,
                                       style="Success.TButton")
        self.start_button.pack(fill="x", pady=(0, 20))

        # 日志区域
        log_frame = ttk.Frame(main_container, style="Secondary.TFrame")
        log_frame.pack(fill="both", expand=True)

        log_header = ttk.Frame(log_frame, style="Secondary.TFrame")
        log_header.pack(fill="x", padx=10, pady=(10, 5))

        ttk.Label(log_header,
                  text="操作日志",
                  style="Subtitle.TLabel").pack(side="left")

        # 日志按钮容器
        log_buttons = ttk.Frame(log_header, style="Secondary.TFrame")
        log_buttons.pack(side="right")

        tk.Button(log_buttons,
                  text="清空",
                  command=self.clear_log,
                  bg=self.colors["bg_tertiary"],
                  fg=self.colors["text_primary"],
                  bd=0,
                  padx=10,
                  pady=2,
                  font=self.fonts["normal"],
                  cursor="hand2").pack(side="left", padx=(5, 0))

        tk.Button(log_buttons,
                  text="保存日志",
                  command=self.save_log,
                  bg=self.colors["bg_tertiary"],
                  fg=self.colors["text_primary"],
                  bd=0,
                  padx=10,
                  pady=2,
                  font=self.fonts["normal"],
                  cursor="hand2").pack(side="left", padx=(5, 0))

        # 日志文本框
        self.log_area = scrolledtext.ScrolledText(
            log_frame,
            bg=self.colors["bg_tertiary"],
            fg=self.colors["text_primary"],
            insertbackground=self.colors["accent_blue"],
            font=self.fonts["mono"],
            bd=0,
            relief="flat",
            padx=10,
            pady=10
        )
        self.log_area.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # 配置标签颜色
        self.log_area.tag_config("success", foreground=self.colors["success"])
        self.log_area.tag_config("error", foreground=self.colors["error"])
        self.log_area.tag_config("warning", foreground=self.colors["warning"])
        self.log_area.tag_config("info", foreground=self.colors["text_secondary"])
        self.log_area.tag_config("path", foreground=self.colors["accent_blue"])

        self.log("=" * 60, "info")
        self.log("智能解压工具已就绪", "success")
        self.log("支持格式: ZIP, TAR, TAR.GZ, TGZ", "info")
        if not DND_AVAILABLE:
            self.log("提示: 安装 tkinterdnd2 可启用拖拽功能 (pip install tkinterdnd2)", "warning")
        self.log("=" * 60, "info")

    def log(self, msg, tag="info"):
        timestamp = time.strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {msg}"

        self.log_area.insert(tk.END, formatted_msg + "\n", tag)
        self.log_area.see(tk.END)
        self.update_idletasks()

    def clear_log(self):
        self.log_area.delete(1.0, tk.END)

    def save_log(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(self.log_area.get(1.0, tk.END))
            self.log(f"日志已保存到: {filename}", "success")

    def choose_file(self):
        path = filedialog.askopenfilename(
            title="选择压缩文件",
            filetypes=[
                ("所有支持的格式", "*.zip *.tar *.tar.gz *.tgz"),
                ("ZIP 文件", "*.zip"),
                ("TAR 文件", "*.tar"),
                ("GZIP 压缩文件", "*.tar.gz *.tgz")
            ]
        )
        if path:
            self.path_var.set(path)
            self.log(f"已选择文件: {path}", "path")

    def choose_dir(self):
        path = filedialog.askdirectory(title="选择文件夹")
        if path:
            self.path_var.set(path)
            self.log(f"已选择文件夹: {path}", "path")

    def enable_drag(self):
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.on_drop)

        # 更新拖拽区域标签
        for widget in self.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Frame) and child.winfo_height() == 120:
                        for label in child.winfo_children():
                            if isinstance(label, tk.Label) and "拖拽" in label.cget("text"):
                                label.configure(text="📤 拖拽文件或文件夹到这里 (已启用)",
                                                fg=self.colors["accent_green"])

    def on_drop(self, event):
        path = event.data.strip("{}")
        self.path_var.set(path)
        self.log(f"拖拽输入: {path}", "path")

    def start(self):
        if self.running:
            messagebox.showwarning("警告", "解压任务正在运行中，请等待完成。")
            return

        path = self.path_var.get()
        if not path or not os.path.exists(path):
            messagebox.showerror("错误", "请选择有效的文件或文件夹路径！")
            return

        delete_after = self.delete_var.get()

        self.running = True
        self.start_button.configure(state="disabled")
        self.status_label.configure(text="解压中...", fg=self.colors["accent_orange"])
        self.progress.start()

        def task():
            try:
                root = os.path.dirname(path) if os.path.isfile(path) else path
                self.log(f"开始递归解压: {root}", "info")
                recursive_extract(root, self.log, delete_after)
            except Exception as e:
                self.log(f"解压过程中出现错误: {str(e)}", "error")
            finally:
                self.after(0, self.finish_task)

        threading.Thread(target=task, daemon=True).start()

    def finish_task(self):
        self.running = False
        self.start_button.configure(state="normal")
        self.status_label.configure(text="完成", fg=self.colors["accent_green"])
        self.progress.stop()


if __name__ == "__main__":
    app = ModernApp()
    app.mainloop()