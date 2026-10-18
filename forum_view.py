import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import database
import utils
import os
import shutil

class ForumPanel(tk.Frame):
    def __init__(self, parent, user_id):
        super().__init__(parent)
        self.user_id = user_id
        self.current_category = None
        self.current_page = None
        self.expanded_items = set()
        self.item_map = {}
        self.selected_item = None

        self.left_frame = tk.Frame(self, width=200)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=8)
        self.left_frame.pack_propagate(False)

        self.right_frame = tk.Frame(self)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Стиль для Treeview
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("Treeview", background="white", fieldbackground="white")
        self.style.map("Treeview", background=[('selected', 'lightblue')])
        
        # Убираем пунктирную рамку фокуса
        self.style.layout("Treeview.Item", [
            ('Treeitem.padding', {'sticky': 'nswe', 'children': [
                ('Treeitem.indicator', {'side': 'left', 'sticky': ''}),
                ('Treeitem.image', {'side': 'left', 'sticky': ''}),
                ('Treeitem.text', {'side': 'left', 'sticky': ''})
            ]})
        ])

        self.tree = ttk.Treeview(self.left_frame, columns=('type',), show='tree')
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        self.tree.bind('<Button-1>', self.on_tree_click)

        # Теги для своих и чужих
        self.tree.tag_configure('my_item', background='#7a2e73')
        self.tree.tag_configure('other_item', background='#d6ce9a')

        self.page_title = tk.Label(self.right_frame, text="Выберите страницу", font=("Arial", 14, "bold"))
        self.page_title.pack(pady=5)

        # Посты
        self.posts_frame = tk.Frame(self.right_frame)
        self.posts_frame.pack(fill=tk.BOTH, expand=True)
        self.posts_text = tk.Text(self.posts_frame, wrap=tk.WORD, height=10, font=("Arial", 10))
        self.posts_scroll = tk.Scrollbar(self.posts_frame, command=self.posts_text.yview)
        self.posts_text.config(yscrollcommand=self.posts_scroll.set)
        self.posts_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.posts_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.posts_text.tag_config('my_post_color', foreground='blue')

        # Файлы
        self.files_frame = tk.Frame(self.right_frame)
        self.files_frame.pack(fill=tk.X, pady=5)
        tk.Label(self.files_frame, text="Прикреплённые файлы:").pack(anchor='w')
        self.files_listbox = tk.Listbox(self.files_frame, height=4, activestyle='none')
        self.files_listbox.pack(fill=tk.X)

        # Кнопки
        self.page_buttons = tk.Frame(self.right_frame)
        self.page_buttons.pack(fill=tk.X)
        
        tk.Button(self.page_buttons, text="Новая категория", command=self.new_category).pack(side=tk.LEFT, padx=2)
        tk.Button(self.page_buttons, text="Новая страница", command=self.new_page).pack(side=tk.LEFT, padx=2)
        tk.Button(self.page_buttons, text="Загрузить файл", command=self.upload_file).pack(side=tk.LEFT, padx=2)
        tk.Button(self.page_buttons, text="Редактировать", command=self.edit_selected_item).pack(side=tk.LEFT, padx=2)
        
        # Скачать файл теперь идет до Удалить
        tk.Button(self.page_buttons, text="Скачать файл", command=self.download_file).pack(side=tk.LEFT, padx=2)
        
        # Создаем, но НЕ пакуем сразу (будут появляться динамически)
        self.btn_delete = tk.Button(self.page_buttons, text="Удалить", command=self.delete_selected_item, fg="red")
        self.btn_clear_posts = tk.Button(self.page_buttons, text="Очистить посты", command=self.clear_posts, fg="red")
        self.btn_delete_file = tk.Button(self.page_buttons, text="Удалить файл", command=self.delete_selected_file, fg="red")

        # Поле ввода поста
        self.post_input_frame = tk.Frame(self.right_frame)
        self.post_input_frame.pack(fill=tk.X, pady=5)
        tk.Label(self.post_input_frame, text="Новый пост:").pack(anchor='w')
        self.post_input = tk.Text(self.post_input_frame, height=4, wrap=tk.WORD, font=("Arial", 10))
        self.post_input.pack(fill=tk.X, padx=0, pady=2)
        # Отправка по Enter
        self.post_input.bind('<Return>', lambda e: self.add_post())
        self.post_input.bind('<Control-Return>', lambda e: self.add_post())

        self.btn_frame = tk.Frame(self.right_frame)
        self.btn_frame.pack(fill=tk.X, pady=(0, 5))
        tk.Button(self.btn_frame, text="Отправить пост", command=self.add_post).pack()

        self.refresh()

    def _update_button_visibility(self):
        """Показывает или скрывает кнопки в зависимости от прав и выделенного элемента."""
        # 1. Сначала прячем все динамические кнопки
        self.btn_delete.pack_forget()
        self.btn_clear_posts.pack_forget()
        self.btn_delete_file.pack_forget()

        can_delete_item = False
        can_modify_page_content = False

        # 2. Проверяем права для СТРАНИЦЫ
        if self.current_page:
            pages = database.get_pages_by_category(self.current_category)
            for pid, title, created_by, _, _ in pages:
                if pid == self.current_page:
                    if created_by == self.user_id or database.is_admin(self.user_id):
                        can_delete_item = True
                        can_modify_page_content = True
                    break
                    
        # 3. Проверяем права для КАТЕГОРИИ
        elif self.current_category:
            categories = database.get_categories()
            for cat_id, name, created_by in categories:
                if cat_id == self.current_category:
                    if created_by == self.user_id or database.is_admin(self.user_id):
                        can_delete_item = True
                    break

        # 4. Показываем кнопки в нужном порядке
        if can_delete_item:
            self.btn_delete.pack(side=tk.LEFT, padx=2)
            
        if can_modify_page_content:
            self.btn_clear_posts.pack(side=tk.LEFT, padx=2)
            self.btn_delete_file.pack(side=tk.LEFT, padx=2)

    def _clean_name(self, name):
        forbidden_suffixes = ["category", "page", "категория", "страница", "кат", "pag"]
        for suffix in forbidden_suffixes:
            name = name.replace(suffix, "").strip()
        return name if name else "Без имени"

    def apply_theme(self, theme_name):
        themes = {
            'light': {'selected': '#3f8376', 'my_bg': '#1E90FF', 'other_bg': '#FFFFFF', 'my_post_fg': '#1E90FF'},
            'dark': {'selected': '#FFA500', 'my_bg': '#00FF7F', 'other_bg': '#3C3C3C', 'my_post_fg': '#00FF7F'},
            'blue': {'selected': '#531e6c', 'my_bg': '#71715b', 'other_bg': "#49658F", 'my_post_fg': '#71715b'}
        }
        theme = themes.get(theme_name, themes['light'])

        self.style.map("Treeview", background=[('selected', theme['selected'])])
        self.tree.tag_configure('my_item', background=theme['my_bg'])
        self.tree.tag_configure('other_item', background=theme['other_bg'])
        self.posts_text.tag_config('my_post_color', foreground=theme['my_post_fg'])

        self.tree.update_idletasks()
        self.refresh()

    def _truncate_text(self, text, max_len=20):
        if len(text) <= max_len:
            return text
        return text[:max_len] + "..."

    def _save_expanded_state(self):
        self.expanded_items.clear()
        for item in self.tree.get_children():
            self._walk_tree(item)

    def _walk_tree(self, item):
        if self.tree.item(item, 'open'):
            values = self.tree.item(item, 'values')
            if values:
                if values[0] == 'category':
                    key = ('category', str(values[1]))
                    self.expanded_items.add(key)
                elif values[0] == 'page':
                    key = ('page', str(values[1]), str(values[2]))
                    self.expanded_items.add(key)
        for child in self.tree.get_children(item):
            self._walk_tree(child)

    def _restore_expanded_state(self):
        for key in self.expanded_items:
            item = self.item_map.get(key)
            if item:
                self.tree.item(item, open=True)
                if key[0] == 'page':
                    parent = self.tree.parent(item)
                    if parent:
                        self.tree.item(parent, open=True)
        self.tree.update_idletasks()

    def _save_selection(self):
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            values = self.tree.item(item, 'values')
            if values and len(values) >= 2:
                if values[0] == 'category':
                    self.selected_item = ('category', str(values[1]))
                elif values[0] == 'page':
                    self.selected_item = ('page', str(values[1]), str(values[2]))
        else:
            self.selected_item = None

    def _restore_selection(self):
        if self.selected_item:
            item = self.item_map.get(self.selected_item)
            if item:
                self.tree.selection_set(item)
                self.tree.focus(item)
                if self.selected_item[0] == 'page':
                    parent = self.tree.parent(item)
                    if parent:
                        self.tree.item(parent, open=True)
                    page_id = int(self.selected_item[1])
                    self.current_page = page_id
                    self.current_category = int(self.selected_item[2])
                    self.load_page_content(page_id)
                elif self.selected_item[0] == 'category':
                    self.current_page = None
                    self.current_category = int(self.selected_item[1])
                    self.page_title.config(text="Выберите страницу")
                    self.posts_text.delete(1.0, tk.END)
                    self.files_listbox.delete(0, tk.END)
            else:
                self.selected_item = None
                self.current_page = None
                self.current_category = None
                self.page_title.config(text="Выберите страницу")
                self.posts_text.delete(1.0, tk.END)
                self.files_listbox.delete(0, tk.END)
        else:
            self.current_page = None
            self.current_category = None
            self.page_title.config(text="Выберите страницу")
            self.posts_text.delete(1.0, tk.END)
            self.files_listbox.delete(0, tk.END)
            
        self._update_button_visibility()

    def refresh(self):
        self._save_expanded_state()
        self._save_selection()

        self.tree.delete(*self.tree.get_children())
        self.item_map.clear()

        categories = database.get_categories()
        for cat_id, name, created_by in categories:
            clean_name = self._clean_name(name)
            display_name = self._truncate_text(clean_name, 20)
            cat_item = self.tree.insert('', 'end', text=display_name, values=('category', cat_id))
            if created_by == self.user_id:
                self.tree.item(cat_item, tags=('my_item',))
            else:
                self.tree.item(cat_item, tags=('other_item',))
            self.item_map[('category', str(cat_id))] = cat_item
            pages = database.get_pages_by_category(cat_id)
            for page_id, title, p_created_by, created_at, updated_at in pages:
                clean_title = self._clean_name(title)
                display_title = self._truncate_text(clean_title, 20)
                page_item = self.tree.insert(cat_item, 'end', text=display_title, values=('page', page_id, cat_id))
                if p_created_by == self.user_id:
                    self.tree.item(page_item, tags=('my_item',))
                else:
                    self.tree.item(page_item, tags=('other_item',))
                self.item_map[('page', str(page_id), str(cat_id))] = page_item

        self._restore_expanded_state()
        self._restore_selection()
        self.tree.update_idletasks()

    def on_tree_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            self.tree.selection_remove(self.tree.selection())
            self.current_page = None
            self.current_category = None
            self.selected_item = None
            self.page_title.config(text="Выберите страницу")
            self.posts_text.delete(1.0, tk.END)
            self.files_listbox.delete(0, tk.END)
            self._update_button_visibility()

    def on_tree_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        item = selection[0]
        values = self.tree.item(item, 'values')
        if not values:
            return
        item_type = values[0]
        if item_type == 'page':
            page_id = int(values[1])
            self.current_page = page_id
            self.current_category = int(values[2])
            self.load_page_content(page_id)
            self.selected_item = ('page', str(page_id), str(self.current_category))
        elif item_type == 'category':
            self.current_category = int(values[1])
            self.current_page = None
            self.selected_item = ('category', str(self.current_category))
            self.page_title.config(text="Выберите страницу")
            self.posts_text.delete(1.0, tk.END)
            self.files_listbox.delete(0, tk.END)
            
        self._update_button_visibility()

    def load_page_content(self, page_id):
        posts = database.get_posts(page_id)
        self.posts_text.config(state=tk.NORMAL)
        self.posts_text.delete(1.0, tk.END)
        for post in posts:
            post_id, user_id, username, display_name, color, content, _ = post
            display = display_name if display_name else username
            if user_id == self.user_id:
                self.posts_text.insert(tk.END, f"[{display}]: ", ('my_post_color',))
                self.posts_text.insert(tk.END, f"{content}\n", ('my_post_color',))
            else:
                self.posts_text.insert(tk.END, f"[{display}]: ", ('color_' + str(post_id),))
                self.posts_text.insert(tk.END, f"{content}\n", ('color_' + str(post_id),))
                self.posts_text.tag_config('color_' + str(post_id), foreground=color)
        self.posts_text.config(state=tk.DISABLED)

        # Сохраняем выделенный файл
        selected_file = None
        selection = self.files_listbox.curselection()
        if selection:
            selected_file = self.files_listbox.get(selection[0])

        self.files_listbox.delete(0, tk.END)
        attachments = database.get_attachments(page_id)
        self.current_attachments = attachments
        for att in attachments:
            att_id, user_id, filename, filepath, filesize, uploaded_at = att
            self.files_listbox.insert(tk.END, f"{filename} ({utils.format_size(filesize)})")

        # Восстанавливаем выделение
        if selected_file:
            for i in range(self.files_listbox.size()):
                if self.files_listbox.get(i) == selected_file:
                    self.files_listbox.selection_set(i)
                    self.files_listbox.activate(i)
                    break

        pages = database.get_pages_by_category(self.current_category)
        for pid, title, _, _, _ in pages:
            if pid == page_id:
                self.page_title.config(text=title)
                break

    def new_category(self):
        name = tk.simpledialog.askstring("Новая категория", "Введите название категории:")
        if name:
            forbidden = ["page", "category", "категория", "страница", "кат", "pag"]
            if any(word in name.lower() for word in forbidden):
                messagebox.showerror("Ошибка", "Название содержит запрещённое слово")
                return
            database.create_category(name, self.user_id)
            self.refresh()

    def edit_selected_item(self):
        forbidden = ["page", "category", "категория", "страница", "кат", "pag"]
        if self.current_page is not None:
            pages = database.get_pages_by_category(self.current_category)
            for pid, title, created_by, _, _ in pages:
                if pid == self.current_page:
                    if created_by == self.user_id or database.is_admin(self.user_id):
                        new_title = tk.simpledialog.askstring("Редактировать страницу", "Новый заголовок:", initialvalue=title)
                        if new_title and new_title != title:
                            if any(word in new_title.lower() for word in forbidden):
                                messagebox.showerror("Ошибка", "Название содержит запрещённое слово")
                                return
                            database.update_page_title(pid, new_title)
                            self.refresh()
                    else:
                        messagebox.showerror("Ошибка", "Нет прав")
                    break
        elif self.current_category is not None:
            categories = database.get_categories()
            current_name = None
            created_by = None
            for cat_id, name, creator in categories:
                if cat_id == self.current_category:
                    current_name = name
                    created_by = creator
                    break
            if current_name is None:
                messagebox.showerror("Ошибка", "Категория не найдена")
                return
            if created_by != self.user_id and not database.is_admin(self.user_id):
                messagebox.showerror("Ошибка", "Нет прав")
                return
            new_name = tk.simpledialog.askstring("Редактировать категорию", "Новое название:", initialvalue=current_name)
            if new_name and new_name.strip():
                if any(word in new_name.lower() for word in forbidden):
                    messagebox.showerror("Ошибка", "Название содержит запрещённое слово")
                    return
                database.update_category_name(self.current_category, new_name.strip())
                self.refresh()
        else:
            messagebox.showerror("Ошибка", "Сначала выберите категорию или страницу")

    def delete_selected_item(self):
        if self.current_page is not None:
            pages = database.get_pages_by_category(self.current_category)
            for pid, title, created_by, _, _ in pages:
                if pid == self.current_page:
                    if created_by == self.user_id or database.is_admin(self.user_id):
                        if messagebox.askyesno("Удаление", f"Удалить страницу '{title}'?"):
                            attachments = database.get_attachments(pid)
                            for att in attachments:
                                if os.path.exists(att[3]):
                                    os.remove(att[3])
                            database.delete_page(pid, self.user_id)
                            self.current_page = None
                            self.refresh()
                    else:
                        messagebox.showerror("Ошибка", "Нет прав")
                    break
        elif self.current_category is not None:
            categories = database.get_categories()
            cat_creator = None
            current_name = None
            for cat_id, name, created_by in categories:
                if cat_id == self.current_category:
                    current_name = name
                    cat_creator = created_by
                    break
            if current_name is None:
                messagebox.showerror("Ошибка", "Категория не найдена")
                return
            if cat_creator != self.user_id and not database.is_admin(self.user_id):
                messagebox.showerror("Ошибка", "Нет прав")
                return
            if messagebox.askyesno("Удаление", f"Удалить категорию '{current_name}' со всеми страницами?"):
                pages = database.get_pages_by_category(self.current_category)
                for page_id, title, _, _, _ in pages:
                    attachments = database.get_attachments(page_id)
                    for att in attachments:
                        if os.path.exists(att[3]):
                            os.remove(att[3])
                    database.delete_page(page_id, self.user_id)
                database.delete_category(self.current_category, self.user_id)
                self.current_category = None
                self.current_page = None
                self.refresh()
        else:
            messagebox.showerror("Ошибка", "Сначала выберите категорию или страницу")

    def new_page(self):
        categories = database.get_categories()
        if not categories:
            messagebox.showerror("Ошибка", "Сначала создайте категорию")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Создание страницы")
        utils.center_window(dialog, 350, 180)
        dialog.resizable(False, False)
        
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        dialog.focus_set()

        tk.Label(dialog, text="Выберите категорию:").pack(pady=5)
        cat_var = tk.StringVar()
        cat_combo = ttk.Combobox(dialog, textvariable=cat_var, state='readonly')
        cat_combo['values'] = [c[1] for c in categories]
        cat_combo.pack(pady=5)

        tk.Label(dialog, text="Заголовок страницы:").pack(pady=5)
        entry_title = tk.Entry(dialog, width=30)
        entry_title.pack(pady=5)

        def create():
            selected = cat_combo.get()
            if not selected:
                messagebox.showerror("Ошибка", "Выберите категорию")
                return
            title = entry_title.get().strip()
            if not title:
                messagebox.showerror("Ошибка", "Введите заголовок")
                return
            forbidden = ["page", "category", "категория", "страница", "кат", "pag"]
            if any(word in title.lower() for word in forbidden):
                messagebox.showerror("Ошибка", "Название содержит запрещённое слово")
                return
            cat_id = None
            for c in categories:
                if c[1] == selected:
                    cat_id = c[0]
                    break
            if cat_id is None:
                messagebox.showerror("Ошибка", "Категория не найдена")
                return
            database.create_page(cat_id, title, self.user_id)
            self.refresh()
            dialog.destroy()

        tk.Button(dialog, text="Создать", command=create).pack(pady=10)

    def upload_file(self):
        if not self.current_page:
            messagebox.showerror("Ошибка", "Выберите страницу")
            return
        limit_mb = database.get_user_upload_limit(self.user_id)
        used_bytes = database.get_user_upload_total(self.user_id)
        if used_bytes >= limit_mb * 1024 * 1024:
            messagebox.showerror("Ошибка", f"Превышен лимит загрузки ({limit_mb} МБ)")
            return

        file_path = filedialog.askopenfilename()
        if file_path:
            filename = os.path.basename(file_path)
            filesize = os.path.getsize(file_path)
            if used_bytes + filesize > limit_mb * 1024 * 1024:
                messagebox.showerror("Ошибка", f"Этот файл превысит лимит. Осталось {(limit_mb*1024*1024 - used_bytes)/1024/1024:.2f} МБ")
                return
            forum_dir = utils.get_upload_path('forum')
            page_dir = os.path.join(forum_dir, str(self.current_page))
            utils.ensure_dir(page_dir)
            dest = os.path.join(page_dir, filename)
            counter = 1
            base, ext = os.path.splitext(filename)
            while os.path.exists(dest):
                dest = os.path.join(page_dir, f"{base}_{counter}{ext}")
                counter += 1
            shutil.copy2(file_path, dest)
            database.add_attachment(self.current_page, self.user_id, os.path.basename(dest), dest, filesize)
            self.refresh()
            messagebox.showinfo("Успех", "Файл загружен")

    def download_file(self):
        selection = self.files_listbox.curselection()
        if not selection:
            messagebox.showerror("Ошибка", "Выберите файл")
            return
        idx = selection[0]
        att = self.current_attachments[idx]
        att_id, user_id, filename, filepath, filesize, uploaded_at = att
        if os.path.exists(filepath):
            save_path = filedialog.asksaveasfilename(defaultextension=os.path.splitext(filename)[1],
                                                     initialfile=filename)
            if save_path:
                shutil.copy2(filepath, save_path)
                messagebox.showinfo("Успех", "Файл сохранён")
        else:
            messagebox.showerror("Ошибка", "Файл не найден на сервере")

    def add_post(self):
        if not self.current_page:
            messagebox.showerror("Ошибка", "Выберите страницу")
            return
        content = self.post_input.get("1.0", tk.END).rstrip("\n")
        if content.strip():
            database.add_post(self.current_page, self.user_id, content)
            self.post_input.delete("1.0", tk.END)
            self.refresh()

    def clear_posts(self):
        """Удаляет все посты на текущей странице (только создатель или админ)."""
        if not self.current_page:
            messagebox.showerror("Ошибка", "Выберите страницу")
            return
        if not self._is_page_creator_or_admin():
            messagebox.showerror("Ошибка", "Нет прав. Только создатель страницы или администратор может очищать посты.")
            return
        
        if messagebox.askyesno("Очистка постов", "Вы уверены, что хотите удалить ВСЕ посты на этой странице? Это действие необратимо."):
            database.clear_page_posts(self.current_page)
            self.load_page_content(self.current_page)
            messagebox.showinfo("Успех", "Все посты удалены.")

    def delete_selected_file(self):
        """Удаляет выбранный файл (только создатель или админ)."""
        if not self.current_page:
            messagebox.showerror("Ошибка", "Выберите страницу")
            return
        if not self._is_page_creator_or_admin():
            messagebox.showerror("Ошибка", "Нет прав. Только создатель страницы или администратор может удалять файлы.")
            return

        selection = self.files_listbox.curselection()
        if not selection:
            messagebox.showerror("Ошибка", "Выберите файл для удаления")
            return

        idx = selection[0]
        att = self.current_attachments[idx]
        att_id, user_id, filename, filepath, filesize, uploaded_at = att

        if messagebox.askyesno("Удаление файла", f"Удалить файл '{filename}'?"):
            database.delete_attachment(att_id, self.user_id)
            self.load_page_content(self.current_page)
            messagebox.showinfo("Успех", "Файл удалён")

    def _is_page_creator_or_admin(self):
        """Проверяет, является ли текущий пользователь создателем текущей страницы или админом."""
        if not self.current_page:
            return False
        pages = database.get_pages_by_category(self.current_category)
        for pid, title, created_by, _, _ in pages:
            if pid == self.current_page:
                return created_by == self.user_id or database.is_admin(self.user_id)
        return False