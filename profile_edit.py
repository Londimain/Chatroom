import tkinter as tk
from tkinter import messagebox, filedialog
import database
import utils
import os
import shutil
from datetime import datetime

class ProfileEdit(tk.Toplevel):
    def __init__(self, parent, user_id):
        super().__init__(parent)
        utils.set_window_icon(self)

        self.transient(parent)
        self.grab_set()
        self.focus_set()

        self.user_id = user_id
        self.user = database.get_user(user_id)
        # Определяем, является ли текущий пользователь администратором
        current_id = parent.user_id if hasattr(parent, 'user_id') else user_id
        self.is_admin = database.is_admin(current_id)
        self.current_user_id = current_id

        self.title("Редактирование профиля")
        utils.center_window(self, 400, 500)
        self.resizable(False, False)

        # Фото
        self.photo_frame = tk.Frame(self)
        self.photo_frame.pack(pady=10)
        self.photo_label = tk.Label(self.photo_frame, text="Нет фото")
        self.photo_label.pack()
        self.current_image = None
        self.load_photo()

        btn_photo = tk.Frame(self)
        btn_photo.pack()
        tk.Button(btn_photo, text="Загрузить фото", command=self.upload_photo).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_photo, text="Удалить фото", command=self.delete_photo).pack(side=tk.LEFT, padx=5)

        # Данные
        form = tk.Frame(self)
        form.pack(pady=10)
        row = 0
        tk.Label(form, text="Логин:", font=("Arial", 12)).grid(row=row, column=0, sticky='e', padx=5, pady=2)
        tk.Label(form, text=self.user['username'], font=("Arial", 12, "bold")).grid(row=row, column=1, sticky='w', padx=5)
        row += 1
        tk.Label(form, text="ФИО:", font=("Arial", 12)).grid(row=row, column=0, sticky='e', padx=5, pady=2)
        self.entry_full_name = tk.Entry(form, width=25)
        self.entry_full_name.insert(0, self.user['full_name'] or '')
        self.entry_full_name.grid(row=row, column=1, sticky='w', padx=5)
        row += 1
        tk.Label(form, text="Должность:", font=("Arial", 12)).grid(row=row, column=0, sticky='e', padx=5, pady=2)
        self.entry_position = tk.Entry(form, width=25)
        self.entry_position.insert(0, self.user['position'] or '')
        self.entry_position.grid(row=row, column=1, sticky='w', padx=5)
        row += 1
        tk.Label(form, text="Телефон:", font=("Arial", 12)).grid(row=row, column=0, sticky='e', padx=5, pady=2)
        self.entry_phone = tk.Entry(form, width=25)
        self.entry_phone.insert(0, self.user['phone'] or '')
        self.entry_phone.grid(row=row, column=1, sticky='w', padx=5)
        row += 1
        tk.Label(form, text="Отображаемый ник:", font=("Arial", 12)).grid(row=row, column=0, sticky='e', padx=5, pady=2)
        self.entry_display_name = tk.Entry(form, width=25)
        self.entry_display_name.insert(0, self.user.get('display_name', ''))
        self.entry_display_name.grid(row=row, column=1, sticky='w', padx=5)
        row += 1
        tk.Label(form, text="Дата регистрации:", font=("Arial", 10)).grid(row=row, column=0, sticky='e', padx=5, pady=2)
        tk.Label(form, text=self.user['registered_at'], font=("Arial", 10)).grid(row=row, column=1, sticky='w', padx=5)

        # Кнопки
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=15)
        
        tk.Button(btn_frame, text="Сохранить изменения", command=self.save_profile).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Сменить пароль", command=self.change_password_dialog).pack(side=tk.LEFT, padx=5)
        
        # Кнопка удаления (только для админа и не для себя самого)
        if self.is_admin and self.user_id != self.current_user_id:
            tk.Button(btn_frame, text="Удалить пользователя", command=self.delete_user, fg="red").pack(side=tk.LEFT, padx=5)
            
        tk.Button(btn_frame, text="Закрыть", command=self.destroy).pack(side=tk.LEFT, padx=5)

    def load_photo(self):
        if self.user['photo_path'] and os.path.exists(self.user['photo_path']):
            img = utils.scale_image(self.user['photo_path'], (150, 150))
            if img:
                self.photo_label.config(image=img, text="")
                self.photo_label.image = img
                self.current_image = img
                return
        self.photo_label.config(image='', text="Нет фото")
        self.current_image = None

    def upload_photo(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif")])
        if file_path:
            avatars_dir = utils.get_upload_path('avatars')
            ext = os.path.splitext(file_path)[1]
            new_name = f"user_{self.user_id}_{int(datetime.now().timestamp())}{ext}"
            dest = os.path.join(avatars_dir, new_name)
            shutil.copy2(file_path, dest)
            database.update_user_profile(self.user_id, self.entry_full_name.get(), self.entry_position.get(),
                                         self.entry_phone.get(), dest)
            self.user['photo_path'] = dest
            self.load_photo()
            messagebox.showinfo("Успех", "Фото загружено")

    def delete_photo(self):
        if self.user['photo_path'] and os.path.exists(self.user['photo_path']):
            os.remove(self.user['photo_path'])
        database.update_user_profile(self.user_id, self.entry_full_name.get(), self.entry_position.get(),
                                     self.entry_phone.get(), None)
        self.user['photo_path'] = None
        self.load_photo()
        messagebox.showinfo("Успех", "Фото удалено")

    def save_profile(self):
        full_name = self.entry_full_name.get().strip()
        position = self.entry_position.get().strip()
        phone = self.entry_phone.get().strip()
        display_name = self.entry_display_name.get().strip()
        if not display_name:
            display_name = self.user['username']
        database.update_user_profile(self.user_id, full_name, position, phone, self.user['photo_path'])
        database.update_display_name(self.user_id, display_name)
        
        # --- Добавить этот блок ---
        # Обновляем заголовок главного окна, если это наш профиль
        main_app = self.master
        if hasattr(main_app, 'label_title') and main_app.user_id == self.user_id:
            main_app.label_title.config(text=f"Чат - {display_name}")
        # ---------------------------

        messagebox.showinfo("Успех", "Профиль обновлён")
        self.destroy()

    def change_password_dialog(self):
        if self.is_admin:
            win = tk.Toplevel(self)
            utils.set_window_icon(win)
            win.transient(self)
            win.grab_set()
            win.focus_set()
            
            win.title("Смена пароля")
            win.geometry("300x180")
            win.resizable(False, False)
            tk.Label(win, text="Новый пароль:").pack(pady=5)
            entry_new = tk.Entry(win, show="*")
            entry_new.pack(pady=5)
            tk.Label(win, text="Повторите пароль:").pack(pady=5)
            entry_confirm = tk.Entry(win, show="*")
            entry_confirm.pack(pady=5)

            def change_admin():
                new = entry_new.get()
                confirm = entry_confirm.get()
                if not new or not confirm:
                    messagebox.showerror("Ошибка", "Заполните все поля")
                    return
                if new != confirm:
                    messagebox.showerror("Ошибка", "Пароли не совпадают")
                    return
                database.admin_change_password(self.user_id, new)
                messagebox.showinfo("Успех", "Пароль изменён")
                win.destroy()

            tk.Button(win, text="Изменить", command=change_admin).pack(pady=10)
        else:
            win = tk.Toplevel(self)
            utils.set_window_icon(win)  # иконка для окна смены пароля (обычный пользователь)
            win.title("Смена пароля")
            win.geometry("300x180")
            win.resizable(False, False)
            tk.Label(win, text="Старый пароль:").pack(pady=5)
            entry_old = tk.Entry(win, show="*")
            entry_old.pack()
            tk.Label(win, text="Новый пароль:").pack(pady=5)
            entry_new = tk.Entry(win, show="*")
            entry_new.pack()
            tk.Label(win, text="Повторите новый:").pack(pady=5)
            entry_confirm = tk.Entry(win, show="*")
            entry_confirm.pack()

            def change():
                old = entry_old.get()
                new = entry_new.get()
                confirm = entry_confirm.get()
                if not old or not new or not confirm:
                    messagebox.showerror("Ошибка", "Заполните все поля")
                    return
                if new != confirm:
                    messagebox.showerror("Ошибка", "Пароли не совпадают")
                    return
                if database.change_password(self.user_id, old, new):
                    messagebox.showinfo("Успех", "Пароль изменён")
                    win.destroy()
                else:
                    messagebox.showerror("Ошибка", "Неверный старый пароль")

            tk.Button(win, text="Изменить", command=change).pack(pady=10)
            
    def delete_user(self):
        """Удаляет пользователя со всеми его данными (только для администратора)."""
        username = self.user['username']
        if messagebox.askyesno(
            "Удаление пользователя", 
            f"Вы уверены, что хотите полностью удалить пользователя '{username}'?\n\n"
            "ВНИМАНИЕ: Все его сообщения, посты, созданные страницы, загруженные файлы и аватарка будут безвозвратно удалены!"
        ):
            success = database.delete_user(self.user_id)
            if success:
                messagebox.showinfo("Успех", f"Пользователь '{username}' удалён.")
                
                # Обновляем списки пользователей в главном окне
                main_app = self.master
                if hasattr(main_app, 'chat_panel') and main_app.chat_panel is not None:
                    main_app.chat_panel.refresh()
                if hasattr(main_app, 'users_list_panel') and main_app.users_list_panel is not None:
                    main_app.users_list_panel.refresh()
                
                self.destroy()
            else:
                messagebox.showerror("Ошибка", "Не удалось удалить пользователя.")