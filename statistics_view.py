import tkinter as tk
from tkinter import ttk, messagebox
import database
import utils
import os
import sys
import subprocess

class StatisticsPanel(tk.Frame):
    def __init__(self, parent, user_id):
        super().__init__(parent)
        self.user_id = user_id
        self.is_admin = database.is_admin(user_id)
        self.selected_user_id = None
        self.details_cache = []

        tk.Label(self, text="Статистика загрузок", font=("Arial", 16)).pack(pady=10)

        self.tree = ttk.Treeview(self, columns=('user', 'total_size', 'count'), show='headings')
        self.tree.heading('user', text='Пользователь')
        self.tree.heading('total_size', text='Всего загружено (МБ)')
        self.tree.heading('count', text='Количество файлов')
        self.tree.column('user', anchor='w')
        self.tree.column('total_size', anchor='center')
        self.tree.column('count', anchor='center')
        self.tree.pack(fill=tk.BOTH, expand=True, pady=5)

        # Привязываем события
        self.tree.bind('<Button-1>', self.on_tree_click)
        self.tree.bind('<<TreeviewSelect>>', self.on_select)

        # Фрейм деталей с большими внешними отступами
        self.details_frame = tk.LabelFrame(self, text="Детали загрузок", padx=5, pady=5)
        self.details_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Контейнер для списка файлов и скроллбара
        self.list_container = tk.Frame(self.details_frame)
        self.list_container.pack(fill=tk.BOTH, expand=True)

        self.details_scroll = tk.Scrollbar(self.list_container)
        self.details_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Заменили Text на Listbox
        self.details_listbox = tk.Listbox(
            self.list_container, 
            yscrollcommand=self.details_scroll.set, 
            font=("Arial", 10), 
            activestyle='none'
        )
        self.details_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.details_scroll.config(command=self.details_listbox.yview)

        # Кнопки действий под списком
        self.action_frame = tk.Frame(self.details_frame)
        self.action_frame.pack(fill=tk.X, pady=(5, 0))

        tk.Button(self.action_frame, text="Открыть файл", command=self.open_file).pack(side=tk.LEFT, padx=5)
        tk.Button(self.action_frame, text="Удалить файл", command=self.delete_file, fg="red").pack(side=tk.LEFT, padx=5)

        self.refresh()

    def on_tree_click(self, event):
        """Обрабатывает клик по таблице. Если клик по пустому месту — снимает выделение."""
        item = self.tree.identify_row(event.y)
        if not item:
            self.tree.selection_remove(self.tree.selection())
            self._clear_details()
            self.selected_user_id = None
            self.details_cache = []

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        users = database.get_all_users()
        self.user_items = {}
        for uid, username, display_name, is_online, is_admin, color in users:
            total_bytes = database.get_user_upload_total(uid)
            count = database.get_user_upload_count(uid)
            total_mb = total_bytes / (1024 * 1024)
            display = display_name if display_name else username
            item = self.tree.insert('', 'end', values=(display, f"{total_mb:.2f}", count), tags=(uid,))
            self.user_items[uid] = item

        if self.selected_user_id is not None and self.selected_user_id in self.user_items:
            item = self.user_items[self.selected_user_id]
            self.tree.selection_set(item)
            self.tree.focus(item)
            if self.details_cache:
                self._fill_details(self.details_cache)
            else:
                self._load_details_for_user(self.selected_user_id)
        else:
            self.tree.selection_remove(self.tree.selection())
            self._clear_details()
            self.selected_user_id = None
            self.details_cache = []

    def _clear_details(self):
        self.details_listbox.delete(0, tk.END)
        self.details_cache = []

    def on_select(self, event):
        selection = self.tree.selection()
        if not selection:
            self._clear_details()
            self.selected_user_id = None
            self.details_cache = []
            return

        item = selection[0]
        uid = self.tree.item(item, 'tags')[0]
        self.selected_user_id = int(uid)
        self._load_details_for_user(self.selected_user_id)

    def _load_details_for_user(self, uid):
        attachments = database.get_all_attachments_with_user()
        
        # 1. Запоминаем, какой файл был выделен
        selected_file = None
        selection = self.details_listbox.curselection()
        if selection:
            selected_file = self.details_listbox.get(selection[0])
            
        self.details_listbox.delete(0, tk.END)
        self.details_cache = []
        for att in attachments:
            if att[1] == uid:
                display = att[3] if att[3] else att[2]
                category = att[9] if len(att) > 9 and att[9] else "Без категории"
                page = att[8] if att[8] else "Без названия"
                line = f"{att[4]} ({utils.format_size(att[5])}) — {category} / {page} ({att[6]})"
                self.details_listbox.insert(tk.END, line)
                self.details_cache.append(att)
        if not self.details_cache:
            self.details_listbox.insert(tk.END, "Нет загруженных файлов")

        # 2. Восстанавливаем выделение
        if selected_file:
            for i in range(self.details_listbox.size()):
                if self.details_listbox.get(i) == selected_file:
                    self.details_listbox.selection_set(i)
                    self.details_listbox.activate(i)
                    break

    def _fill_details(self, cache):
        # 1. Запоминаем, какой файл был выделен
        selected_file = None
        selection = self.details_listbox.curselection()
        if selection:
            selected_file = self.details_listbox.get(selection[0])
            
        self.details_listbox.delete(0, tk.END)
        if cache:
            for att in cache:
                display = att[3] if att[3] else att[2]
                category = att[9] if len(att) > 9 and att[9] else "Без категории"
                page = att[8] if att[8] else "Без названия"
                line = f"{att[4]} ({utils.format_size(att[5])}) — {category} / {page} ({att[6]})"
                self.details_listbox.insert(tk.END, line)
        else:
            self.details_listbox.insert(tk.END, "Нет загруженных файлов")

        # 2. Восстанавливаем выделение
        if selected_file:
            for i in range(self.details_listbox.size()):
                if self.details_listbox.get(i) == selected_file:
                    self.details_listbox.selection_set(i)
                    self.details_listbox.activate(i)
                    break

    def open_file(self):
        """Открывает выбранный файл с помощью программы по умолчанию."""
        selection = self.details_listbox.curselection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите файл для открытия")
            return
        
        idx = selection[0]
        if not self.details_cache or idx >= len(self.details_cache):
            return
            
        att = self.details_cache[idx]
        # att[10] - это путь к файлу (filepath), который мы добавили в database.py
        filepath = att[10]
        
        if os.path.exists(filepath):
            try:
                if sys.platform == "win32":
                    os.startfile(filepath)
                elif sys.platform == "darwin": # macOS
                    subprocess.call(["open", filepath])
                else: # Linux
                    subprocess.call(["xdg-open", filepath])
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть файл:\n{e}")
        else:
            messagebox.showerror("Ошибка", "Файл не найден на диске (возможно, он был удалён).")

    def delete_file(self):
        """Удаляет выбранный файл с подтверждением."""
        selection = self.details_listbox.curselection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите файл для удаления")
            return

        idx = selection[0]
        if not self.details_cache or idx >= len(self.details_cache):
            return
            
        att = self.details_cache[idx]
        att_id = att[0]
        filename = att[4]

        if messagebox.askyesno("Удаление файла", f"Вы уверены, что хотите удалить файл '{filename}'?\nЭто действие необратимо."):
            # В database.delete_attachment уже встроена проверка на права администратора
            if database.delete_attachment(att_id, self.user_id):
                messagebox.showinfo("Успех", "Файл удалён")
                self.refresh() # Обновляем таблицу и детали
            else:
                messagebox.showerror("Ошибка", "Не удалось удалить файл (нет прав или файл не найден в БД).")

    def apply_theme(self, theme_name):
        style = ttk.Style()
        style.theme_use('clam')
        themes = {
            'light': {'bg': '#f0f0f0', 'button_bg': '#e0e0e0'},
            'dark': {'bg': '#2b2b2b', 'button_bg': '#3c3c3c'},
            'blue': {'bg': '#d9e4f5', 'button_bg': '#b0c4de'}
        }
        theme = themes.get(theme_name, themes['light'])
        style.configure("Treeview.Heading", background=theme['button_bg'], foreground="black", relief="raised")
        style.configure("Treeview", background=theme['bg'], fieldbackground=theme['bg'])
        self.tree.update()
        try:
            self.details_listbox.config(bg=theme['bg'])
        except:
            pass