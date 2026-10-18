import tkinter as tk
from tkinter import messagebox
import database
import utils
import os

class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Чат - Вход")
        utils.center_window(self, 350, 250)
        self.resizable(False, False)

        # Устанавливаем иконку окна (если файл существует)
        ico_path = utils.resource_path('ico/chat.ico')
        if os.path.exists(ico_path):
            self.iconbitmap(ico_path)

        # Заголовок
        tk.Label(self, text="Добро пожаловать в Чат!", font=("Arial", 18)).pack(pady=20)

        frame = tk.Frame(self)
        frame.pack(pady=10)

        tk.Label(frame, text="Логин:", font=("Arial", 12)).grid(row=0, column=0, padx=10, pady=5, sticky='e')
        self.entry_login = tk.Entry(frame, width=20, font=("Arial", 12))
        self.entry_login.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(frame, text="Пароль:", font=("Arial", 12)).grid(row=1, column=0, padx=10, pady=5, sticky='e')
        self.entry_password = tk.Entry(frame, width=20, font=("Arial", 12), show="*")
        self.entry_password.grid(row=1, column=1, padx=10, pady=5)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=20)

        tk.Button(btn_frame, text="Войти", width=12, command=self.login).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Регистрация", width=12, command=self.register).pack(side=tk.LEFT, padx=5)

        self.bind('<Return>', lambda e: self.login())

    def login(self):
        username = self.entry_login.get().strip()
        password = self.entry_password.get().strip()
        if not username or not password:
            messagebox.showerror("Ошибка", "Введите логин и пароль")
            return
        user_id, is_admin = database.authenticate(username, password)
        if user_id:
            self.destroy()
            from main_app import MainApp
            app = MainApp(user_id)
            app.mainloop()
        else:
            messagebox.showerror("Ошибка", "Неверный логин или пароль")

    def register(self):
        from register_window import RegisterWindow
        RegisterWindow(self)