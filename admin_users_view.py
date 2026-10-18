import tkinter as tk
from tkinter import ttk, messagebox
import database
import utils

class AdminUsersPanel(tk.Frame):
    def __init__(self, parent, current_user_id):
        super().__init__(parent)
        self.current_user_id = current_user_id
        
        # Заголовок
        tk.Label(self, text="Управление пользователями", font=("Arial", 16, "bold")).pack(pady=10)

        # Стиль для таблицы
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("Treeview", background="white", fieldbackground="white")
        self.style.map("Treeview", background=[('selected', '#3f8376')])
        
        # Таблица (Treeview)
        columns = ('id', 'login', 'nick', 'status', 'role', 'registered')
        self.tree = ttk.Treeview(self, columns=columns, show='headings')
        
        self.tree.heading('id', text='ID')
        self.tree.heading('login', text='Логин')
        self.tree.heading('nick', text='Ник')
        self.tree.heading('status', text='Статус')
        self.tree.heading('role', text='Роль')
        self.tree.heading('registered', text='Дата регистрации')
        
        self.tree.column('id', width=40, anchor='center')
        self.tree.column('login', width=150, anchor='w')
        self.tree.column('nick', width=150, anchor='w')
        self.tree.column('status', width=80, anchor='center')
        self.tree.column('role', width=100, anchor='center')
        self.tree.column('registered', width=150, anchor='center')
        
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Двойной клик для быстрого открытия профиля
        self.tree.bind('<Double-1>', lambda e: self.open_profile())

        # Кнопки управления
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(btn_frame, text="Обновить список", command=self.refresh).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Открыть профиль", command=self.open_profile).pack(side=tk.LEFT, padx=5)
        
        self.btn_toggle_admin = tk.Button(btn_frame, text="Вкл/Выкл админа", command=self.toggle_admin, fg="#084974")
        self.btn_toggle_admin.pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="Удалить пользователя", command=self.delete_user, fg="red").pack(side=tk.LEFT, padx=5)

        self.refresh()

    def refresh(self):
        """Обновляет таблицу пользователей."""
        # Сохраняем выделение
        selected_id = None
        selection = self.tree.selection()
        if selection:
            selected_id = self.tree.item(selection[0], 'values')[0]

        for row in self.tree.get_children():
            self.tree.delete(row)

        users = database.get_all_users_detailed()
        for user in users:
            uid, username, display_name, is_online, is_admin, registered_at = user
            
            display_nick = display_name if display_name else username
            status = "🟢 Онлайн" if is_online else "⚪ Офлайн"
            role = "Админ ★" if is_admin else "Пользователь"
            
            # Обрезаем дату регистрации до дней (если она слишком длинная)
            reg_date = str(registered_at).split('.')[0] if registered_at else ""

            item = self.tree.insert('', 'end', values=(uid, username, display_nick, status, role, reg_date))
            
            # Восстанавливаем выделение
            if selected_id and str(uid) == str(selected_id):
                self.tree.selection_set(item)
                self.tree.focus(item)

    def get_selected_user_id(self):
        """Вспомогательный метод для получения ID выбранного пользователя."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Сначала выберите пользователя в таблице.")
            return None
        return int(self.tree.item(selection[0], 'values')[0])

    def open_profile(self):
        """Открывает профиль выбранного пользователя."""
        uid = self.get_selected_user_id()
        if uid:
            # Обращаемся к главному окну, чтобы открыть профиль
            main_app = self.winfo_toplevel()
            if hasattr(main_app, 'open_profile'):
                main_app.open_profile(uid)

    def toggle_admin(self):
        """Выдает или забирает права администратора."""
        uid = self.get_selected_user_id()
        if not uid:
            return
            
        if uid == self.current_user_id:
            messagebox.showerror("Ошибка", "Вы не можете забрать права администратора у самого себя!")
            return

        # Получаем текущий статус
        user = database.get_user(uid)
        current_status = user['is_admin']
        
        action = "забрать" if current_status else "выдать"
        if messagebox.askyesno("Смена роли", f"Вы уверены, что хотите {action} права администратора у пользователя '{user['username']}'?"):
            database.set_admin_status(uid, not current_status)
            self.refresh()
            messagebox.showinfo("Успех", "Роль пользователя изменена.")

    def delete_user(self):
        """Удаляет пользователя."""
        uid = self.get_selected_user_id()
        if not uid:
            return

        if uid == self.current_user_id:
            messagebox.showerror("Ошибка", "Вы не можете удалить самого себя!")
            return

        user = database.get_user(uid)
        if messagebox.askyesno(
            "Удаление пользователя", 
            f"Вы уверены, что хотите ПОЛНОСТЬЮ удалить пользователя '{user['username']}'?\n\n"
            "ВНИМАНИЕ: Все его сообщения, файлы и аватарка будут безвозвратно удалены!"
        ):
            success = database.delete_user(uid)
            if success:
                messagebox.showinfo("Успех", "Пользователь удалён.")
                self.refresh()
                # Обновляем список в чате, если он открыт
                main_app = self.winfo_toplevel()
                if hasattr(main_app, 'chat_panel') and main_app.chat_panel is not None:
                    main_app.chat_panel.refresh()
            else:
                messagebox.showerror("Ошибка", "Не удалось удалить пользователя.")

    def apply_theme(self, theme_name):
        """Применяет цвета темы к таблице."""
        themes = {
            'light': {'bg': '#f0f0f0', 'button_bg': '#e0e0e0'},
            'dark': {'bg': '#2b2b2b', 'button_bg': '#3c3c3c'},
            'blue': {'bg': '#d9e4f5', 'button_bg': '#b0c4de'}
        }
        theme = themes.get(theme_name, themes['light'])
        self.style.configure("Treeview.Heading", background=theme['button_bg'], foreground="black", relief="raised")
        self.style.configure("Treeview", background=theme['bg'], fieldbackground=theme['bg'])
        self.tree.update()