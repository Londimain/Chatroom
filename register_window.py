import tkinter as tk
from tkinter import messagebox
import database
import utils

class RegisterWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        utils.set_window_icon(self)

        self.transient(parent)
        self.grab_set()
        self.focus_set()

        self.parent = parent
        self.title("Регистрация")
        utils.center_window(self, 400, 250)
        self.resizable(False, False)
        
        tk.Label(self, text="Создание аккаунта", font=("Arial", 16)).pack(pady=10)
        
        frame = tk.Frame(self)
        frame.pack(pady=10)
        
        tk.Label(frame, text="Логин:", font=("Arial", 12)).grid(row=0, column=0, padx=10, pady=5, sticky='e')
        self.entry_login = tk.Entry(frame, width=20, font=("Arial", 12))
        self.entry_login.grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(frame, text="Пароль:", font=("Arial", 12)).grid(row=1, column=0, padx=10, pady=5, sticky='e')
        self.entry_password = tk.Entry(frame, width=20, font=("Arial", 12), show="*")
        self.entry_password.grid(row=1, column=1, padx=10, pady=5)
        
        tk.Label(frame, text="Подтвердите пароль:", font=("Arial", 12)).grid(row=2, column=0, padx=10, pady=5, sticky='e')
        self.entry_confirm = tk.Entry(frame, width=20, font=("Arial", 12), show="*")
        self.entry_confirm.grid(row=2, column=1, padx=10, pady=5)
        
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="Зарегистрироваться", width=16, command=self.register).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Отмена", width=10, command=self.destroy).pack(side=tk.LEFT, padx=5)
    
    def register(self):
        login = self.entry_login.get().strip()
        password = self.entry_password.get().strip()
        confirm = self.entry_confirm.get().strip()
        
        if not login or not password:
            messagebox.showerror("Ошибка", "Заполните все поля")
            return
        if password != confirm:
            messagebox.showerror("Ошибка", "Пароли не совпадают")
            return
        
        success, msg, user_id = database.register_user(login, password)
        if success:
            database.set_online_status(user_id, True)
            database.update_last_seen(user_id)
            messagebox.showinfo("Успех", "Регистрация успешна! Выполняется вход...")
            # Закрываем окно регистрации и окно входа
            self.destroy()
            self.parent.destroy()  # закрываем родительское окно (вход)
            from main_app import MainApp
            app = MainApp(user_id)
            app.mainloop()
        else:
            messagebox.showerror("Ошибка", msg)