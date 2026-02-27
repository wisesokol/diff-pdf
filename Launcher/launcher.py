import json
import os
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox


CONFIG_FILE = "launcher_config.json"


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(data):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        messagebox.showerror("Ошибка сохранения", f"Не удалось сохранить настройки:\n{e}")


class LauncherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("diff-pdf Launcher")
        self.resizable(False, False)

        self.program_path_var = tk.StringVar()
        self.args_var = tk.StringVar(value="--binary=5 --view")
        self.file1_var = tk.StringVar()
        self.file2_var = tk.StringVar()

        self._load_initial_config()
        self._build_ui()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _load_initial_config(self):
        cfg = load_config()
        self.program_path_var.set(cfg.get("program_path", ""))
        self.args_var.set(cfg.get("args", self.args_var.get()))
        self.file1_var.set(cfg.get("file1", ""))
        self.file2_var.set(cfg.get("file2", ""))

    def _build_ui(self):
        padding_x = 10
        padding_y = 5

        # Program selection
        tk.Label(self, text="Программа (diff-pdf.exe):").grid(
            row=0, column=0, sticky="w", padx=padding_x, pady=(padding_y, 0)
        )
        prog_frame = tk.Frame(self)
        prog_frame.grid(row=1, column=0, columnspan=2, sticky="we", padx=padding_x)
        prog_entry = tk.Entry(prog_frame, textvariable=self.program_path_var, width=50)
        prog_entry.pack(side="left", fill="x", expand=True)
        tk.Button(prog_frame, text="Обзор...", command=self.browse_program).pack(
            side="left", padx=(5, 0)
        )

        # Args
        tk.Label(self, text="Аргументы запуска:").grid(
            row=2, column=0, sticky="w", padx=padding_x, pady=(padding_y, 0)
        )
        args_entry = tk.Entry(self, textvariable=self.args_var, width=50)
        args_entry.grid(row=3, column=0, columnspan=2, sticky="we", padx=padding_x)

        # File 1
        tk.Label(self, text="Файл 1 (PDF):").grid(
            row=4, column=0, sticky="w", padx=padding_x, pady=(padding_y, 0)
        )
        file1_frame = tk.Frame(self)
        file1_frame.grid(row=5, column=0, columnspan=2, sticky="we", padx=padding_x)
        file1_entry = tk.Entry(file1_frame, textvariable=self.file1_var, width=50)
        file1_entry.pack(side="left", fill="x", expand=True)
        tk.Button(file1_frame, text="Обзор...", command=self.browse_file1).pack(
            side="left", padx=(5, 0)
        )

        # File 2
        tk.Label(self, text="Файл 2 (PDF):").grid(
            row=6, column=0, sticky="w", padx=padding_x, pady=(padding_y, 0)
        )
        file2_frame = tk.Frame(self)
        file2_frame.grid(row=7, column=0, columnspan=2, sticky="we", padx=padding_x)
        file2_entry = tk.Entry(file2_frame, textvariable=self.file2_var, width=50)
        file2_entry.pack(side="left", fill="x", expand=True)
        tk.Button(file2_frame, text="Обзор...", command=self.browse_file2).pack(
            side="left", padx=(5, 0)
        )

        # Run button
        run_button = tk.Button(self, text="Запустить diff-pdf", command=self.run_diff_pdf)
        run_button.grid(row=8, column=0, columnspan=2, pady=(padding_y * 2, padding_y))

    def browse_program(self):
        path = filedialog.askopenfilename(
            title="Выберите diff-pdf.exe",
            filetypes=[("EXE файлы", "*.exe"), ("Все файлы", "*.*")],
        )
        if path:
            self.program_path_var.set(path)

    def browse_file1(self):
        path = filedialog.askopenfilename(
            title="Выберите файл 1 (PDF)",
            filetypes=[("PDF файлы", "*.pdf"), ("Все файлы", "*.*")],
        )
        if path:
            self.file1_var.set(path)

    def browse_file2(self):
        path = filedialog.askopenfilename(
            title="Выберите файл 2 (PDF)",
            filetypes=[("PDF файлы", "*.pdf"), ("Все файлы", "*.*")],
        )
        if path:
            self.file2_var.set(path)

    def _build_command(self):
        program = self.program_path_var.get().strip()
        args = self.args_var.get().strip()
        file1 = self.file1_var.get().strip()
        file2 = self.file2_var.get().strip()

        if not program:
            raise ValueError("Не указан путь к программе diff-pdf.exe")
        if not os.path.isfile(program):
            raise ValueError("Файл программы не найден:\n" + program)
        if not file1:
            raise ValueError("Не выбран файл 1 (PDF)")
        if not file2:
            raise ValueError("Не выбран файл 2 (PDF)")
        if not os.path.isfile(file1):
            raise ValueError("Файл 1 не существует:\n" + file1)
        if not os.path.isfile(file2):
            raise ValueError("Файл 2 не существует:\n" + file2)

        # Разбиваем аргументы по пробелам, без shell
        import shlex

        cmd = [program]
        if args:
            cmd += shlex.split(args)
        cmd.append(file1)
        cmd.append(file2)
        return cmd

    def run_diff_pdf(self):
        try:
            cmd = self._build_command()
        except ValueError as e:
            messagebox.showerror("Ошибка параметров", str(e))
            return
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка построения команды:\n{e}")
            return

        # Сохраняем настройки перед запуском
        self._save_current_config()

        try:
            # Запуск без открытия отдельного окна консоли (GUI-режим)
            subprocess.Popen(cmd, shell=False)
        except Exception as e:
            messagebox.showerror("Ошибка запуска", f"Не удалось запустить diff-pdf:\n{e}")

    def _save_current_config(self):
        data = {
            "program_path": self.program_path_var.get().strip(),
            "args": self.args_var.get().strip(),
            "file1": self.file1_var.get().strip(),
            "file2": self.file2_var.get().strip(),
        }
        save_config(data)

    def on_close(self):
        self._save_current_config()
        self.destroy()


def main():
    app = LauncherApp()
    app.mainloop()


if __name__ == "__main__":
    main()

