import tkinter as tk
from tkinter import messagebox
import database
import utils
import os

class ProfileView(tk.Toplevel):
    def __init__(self, parent, current_user_id, viewed_user_id):
        super().__init__(parent)
        utils.set_window_icon(self)
        
        self.transient(parent)
        self.grab_set()
        self.focus_set()

        self.parent = parent
        self.current_user_id = current_user_id
        self.viewed_user_id = viewed_user_id  # <--- Вот это добавлено
        self.title("Профиль пользователя")
        utils.center_window(self, 400, 500)
        self.resizable(False, False)

        user = database.get_user(viewed_user_id)
        if not user:
            messagebox.showerror("Ошибка", "Пользователь не найден")
            self.destroy()
            return

        self.user = user
        self.current_image = None

        # Фото
        self.photo_label = tk.Label(self, text="Нет фото")
        self.photo_label.pack(pady=10)
        if user['photo_path'] and os.path.exists(user['photo_path']):
            img = utils.scale_image(user['photo_path'], (150, 150))
            if img:
                self.photo_label.config(image=img, text="")
                self.photo_label.image = img
                self.current_image = img

        # Имя
        display = user['display_name'] if user['display_name'] else user['username']
        tk.Label(self, text=display, font=("Arial", 16, "bold")).pack()
        if user['is_admin']:
            tk.Label(self, text="(Администратор)", font=("Arial", 10, "italic")).pack()

        # Данные
        info_frame = tk.Frame(self)
        info_frame.pack(pady=10)
        tk.Label(info_frame, text=f"ФИО: {user['full_name'] or 'Не указано'}", font=("Arial", 12)).pack(anchor='w')
        tk.Label(info_frame, text=f"Должность: {user['position'] or 'Не указана'}", font=("Arial", 12)).pack(anchor='w')
        tk.Label(info_frame, text=f"Телефон: {user['phone'] or 'Не указан'}", font=("Arial", 12)).pack(anchor='w')
        tk.Label(info_frame, text=f"Дата регистрации: {user['registered_at']}", font=("Arial", 10)).pack(anchor='w')
        status = "Онлайн" if user['is_online'] else "Офлайн"
        tk.Label(info_frame, text=f"Статус: {status}", font=("Arial", 10)).pack(anchor='w')

        # Кнопки
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)

        # Разрешаем редактировать, если это свой профиль или текущий пользователь — администратор
        if current_user_id == viewed_user_id or database.is_admin(current_user_id):
            tk.Button(btn_frame, text="Редактировать", command=self.edit_profile).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Закрыть", command=self.destroy).pack(side=tk.LEFT, padx=5)

    def edit_profile(self):
        self.destroy()
        from profile_edit import ProfileEdit
        # Передаём ID просматриваемого пользователя (редактируем именно его)
        ProfileEdit(self.parent, self.viewed_user_id)