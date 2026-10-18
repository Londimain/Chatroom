import tkinter as tk
from tkinter import ttk, messagebox
import database
import utils
import os
import re
from users_list import UsersList

class ChatPanel(tk.Frame):
    def __init__(self, parent, user_id):
        super().__init__(parent)
        self.user_id = user_id
        self.last_message_id = 0
        self.user_data = database.get_user(user_id)
        
        self.emoji_window = None
        self.emoji_images = {}  
        self.emoji_paths = {}   
        
        self.input_images = {}      
        self.input_images_refs = [] 
        
        self.scan_emojis()

        # Левая панель (список пользователей)
        self.left_frame = tk.Frame(self, width=200)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=2, pady=2)
        self.left_frame.pack_propagate(False)
        
        # Правая панель (чат)
        self.right_frame = tk.Frame(self)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        self.users_list = UsersList(self.left_frame, self.user_id, on_select=self.on_user_select)
        self.users_list.pack(fill=tk.BOTH, expand=True)
        
        # ==========================================
        # ПАНЕЛЬ ВВОДА (внизу)
        # ==========================================
        self.input_frame = tk.Frame(self.right_frame)
        # Добавлен отступ справа (0, 10), чтобы панель не прилипала к краю окна
        self.input_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5, padx=(0, 10)) 
        
        # 1. Кнопка отправки (справа)
        self.btn_send = tk.Button(self.input_frame, text="Отправить", command=self.send_message, padx=15, pady=4)
        self.btn_send.pack(side=tk.RIGHT, padx=5)
        
        # 2. Кнопка смайликов (слева)
        icon = self.get_emoji("1") if "1" in self.emoji_paths else "😀"
        self.btn_emoji = tk.Button(self.input_frame, image=icon, text="Смайлы", compound=tk.LEFT, 
                                   command=self.open_emoji_picker, padx=10, pady=2)
        self.btn_emoji.pack(side=tk.LEFT, padx=(5, 5))
        
        # Кнопка очистки чата (только для админа)
        if database.is_admin(self.user_id):
            self.btn_clear_chat = tk.Button(self.input_frame, text="Очистить чат", command=self.clear_chat, fg="red", padx=5, pady=4)
            self.btn_clear_chat.pack(side=tk.LEFT, padx=(5, 0))
        
        # 3. Поле ввода (по центру)
        self.entry_message = tk.Text(
            self.input_frame, 
            font=("Segoe UI", 11), 
            height=1, 
            wrap='none', 
            bd=1, 
            relief='sunken',
            padx=5,
            pady=2
        )
        self.entry_message.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        self.entry_message.bind('<Return>', self.on_enter_pressed)
        
        # ==========================================
        # ОБЛАСТЬ СООБЩЕНИЙ (сверху)
        # ==========================================
        self.messages_text = tk.Text(
            self.right_frame, 
            wrap=tk.WORD, 
            state=tk.DISABLED, 
            font=("Segoe UI", 10),
            spacing1=2,
            spacing3=6,
            padx=10,   # Внутренний отступ текста от левой/правой рамки
            pady=10,   # Внутренний отступ текста от верхней/нижней рамки
            bd=0       # Убираем стандартную рамку для аккуратности
        )
        # Добавлены отступы справа (0, 10) и сверху (5, 0) для идеального выравнивания
        self.messages_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=(0, 10), pady=(5, 0))
        
        self.refresh()

    def scan_emojis(self):
        smile_dir = utils.resource_path('Smile/origin-style')
        if not os.path.exists(smile_dir):
            print(f"Папка не найдена: {smile_dir}")
            return

        for i in range(1, 1000):
            path = os.path.join(smile_dir, f'{i}.png')
            if os.path.exists(path):
                self.emoji_paths[str(i)] = path

    def get_emoji(self, emoji_id):
        emoji_id = str(emoji_id)
        if emoji_id not in self.emoji_images:
            path = self.emoji_paths.get(emoji_id)
            if path and os.path.exists(path):
                img = utils.scale_image(path, (24, 24))
                if img:
                    img.name = f"smile_{emoji_id}"
                    self.emoji_images[emoji_id] = img
        return self.emoji_images.get(emoji_id)

    def on_enter_pressed(self, event):
        self.send_message()
        return "break"

    def on_user_select(self, user_id):
        parent = self.winfo_toplevel()
        if hasattr(parent, 'open_profile'):
            parent.open_profile(user_id)
        else:
            from profile_view import ProfileView
            ProfileView(parent, self.user_id, user_id)
            
    def send_message(self):
        dump = self.entry_message.dump("1.0", "end-1c", text=True, image=True)
        result_text = ""
        
        for item in dump:
            if item[0] == "text":
                result_text += item[1]
            elif item[0] == "image":
                img_name = item[1]
                if img_name in self.input_images:
                    emoji_id = self.input_images[img_name]
                    result_text += f"[smile:{emoji_id}]"

        if result_text.strip():
            try:
                result_text = result_text.encode('utf-16', 'surrogatepass').decode('utf-16')
            except Exception:
                pass
            
            database.add_message(self.user_id, result_text)
            
            self.entry_message.delete("1.0", tk.END)
            self.input_images.clear()
            self.input_images_refs.clear()
            
            self.refresh()
    
    def refresh(self):
        self.users_list.refresh()
        messages = database.get_messages(100)
        
        # --- ЛОГИКА ЗВУКОВЫХ УВЕДОМЛЕНИЙ ---
        if messages:
            latest_msg = messages[-1]
            latest_id = latest_msg[0]
            latest_user_id = latest_msg[1]

            # Если это не первая загрузка чата и ID нового сообщения больше предыдущего
            if self.last_message_id != 0 and latest_id > self.last_message_id:
                # Если сообщение от ДРУГОГО пользователя
                if latest_user_id != self.user_id:
                    user_settings = database.get_user(self.user_id)
                    if user_settings.get('sound_enabled', 1):
                        utils.play_sound(user_settings.get('sound_path', ''))
            
            self.last_message_id = latest_id
        # -----------------------------------

        self.messages_text.config(state=tk.NORMAL)
        self.messages_text.delete(1.0, tk.END)
        
        for msg in messages:
            msg_id, uid, username, display_name, color, text, ts = msg
            display = display_name if display_name else username
            tag_name = f"color_{msg_id}"
            
            self.messages_text.insert(tk.END, f"[{display}]: ", (tag_name,))
            
            parts = re.split(r'(\[smile:\d+\])', text)
            for i, part in enumerate(parts):
                match = re.match(r'\[smile:(\d+)\]', part)
                if match:
                    emoji_id = match.group(1)
                    img = self.get_emoji(emoji_id)
                    if img:
                        self.messages_text.image_create(tk.END, image=img)
                        if i + 1 < len(parts) and parts[i+1] and not parts[i+1].startswith(" "):
                            self.messages_text.insert(tk.END, " ")
                    else:
                        self.messages_text.insert(tk.END, part)
                else:
                    self.messages_text.insert(tk.END, part)
            
            self.messages_text.insert(tk.END, "\n")
            self.messages_text.tag_config(tag_name, foreground=color)
        
        self.messages_text.config(state=tk.DISABLED)
        self.messages_text.see(tk.END)

    def open_emoji_picker(self):
        if self.emoji_window is not None and self.emoji_window.winfo_exists():
            self.emoji_window.lift()
            return

        self.emoji_window = tk.Toplevel(self)
        utils.set_window_icon(self.emoji_window)
        self.emoji_window.title("Смайлики")
        self.emoji_window.resizable(False, False)
        
        utils.center_window(self.emoji_window, 400, 300)
        self.emoji_window.transient(self.winfo_toplevel())
        self.emoji_window.grab_set()

        # Создаем холст и скроллбар
        canvas = tk.Canvas(self.emoji_window, borderwidth=0, highlightthickness=0, bg="#f0f0f0")
        scrollbar = tk.Scrollbar(self.emoji_window, orient="vertical", command=canvas.yview)
        
        canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Обработка клика по холсту (находим ближайшую картинку)
        def on_canvas_click(event):
            item = canvas.find_closest(event.x, event.y)
            if item:
                tags = canvas.gettags(item)
                for tag in tags:
                    if tag.startswith("smile_"):
                        emoji_id = tag.replace("smile_", "")
                        self.insert_emoji(emoji_id)
                        return
        canvas.bind("<Button-1>", on_canvas_click)

        # Прокрутка колесиком мыши
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.emoji_window.bind("<MouseWheel>", _on_mousewheel)

        # Показываем надпись "Загрузка..." пока грузятся картинки
        loading_text = canvas.create_text(190, 130, text="Загрузка смайликов...", font=("Arial", 12), fill="gray")

        # Получаем все ID смайликов и сортируем их
        sorted_ids = sorted(self.emoji_paths.keys(), key=int)
        
        # Используем переменные для порционной загрузки
        state = {"index": 0, "chunk_size": 50}
        
        def load_next_chunk():
            # Если окно закрыли во время загрузки - прекращаем
            if not self.emoji_window or not self.emoji_window.winfo_exists():
                return
            
            # Удаляем надпись "Загрузка..." при первом запуске
            if state["index"] == 0:
                canvas.delete(loading_text)

            end_index = min(state["index"] + state["chunk_size"], len(sorted_ids))
            
            for i in range(state["index"], end_index):
                emoji_id = sorted_ids[i]
                img = self.get_emoji(emoji_id)
                if img:
                    # Вычисляем координаты для сетки (12 колонок)
                    row = i // 12
                    col = i % 12
                    x = col * 32 + 16
                    y = row * 32 + 16
                    
                    # Рисуем картинку на холсте и вешаем на нее тег
                    canvas.create_image(x, y, image=img, tags=f"smile_{emoji_id}")
            
            # Обновляем ползунок прокрутки
            canvas.configure(scrollregion=canvas.bbox("all"))
            
            state["index"] = end_index
            
            # Если остались еще смайлики, загружаем следующую пачку через 10 мс
            if state["index"] < len(sorted_ids):
                self.emoji_window.after(10, load_next_chunk)

        # Запускаем процесс загрузки
        self.emoji_window.after(10, load_next_chunk)
        
    def clear_chat(self):
        """Очищает всю историю чата (только для админа)."""
        if not database.is_admin(self.user_id):
            return
            
        if messagebox.askyesno("Очистка чата", "Вы уверены, что хотите удалить ВСЮ историю сообщений?\nЭто действие необратимо."):
            database.clear_all_messages()
            self.refresh()
            messagebox.showinfo("Успех", "Чат очищен.")

    def insert_emoji(self, emoji_id):
        emoji_id = str(emoji_id)
        path = self.emoji_paths.get(emoji_id)
        if path and os.path.exists(path):
            img_small = utils.scale_image(path, (16, 16))
            if img_small:
                current_text = self.entry_message.get("1.0", "end-1c")
                if current_text and not current_text.endswith(" "):
                    self.entry_message.insert(tk.END, " ")
                
                self.entry_message.image_create(tk.END, image=img_small)
                
                tk_img_name = str(img_small)
                self.input_images[tk_img_name] = emoji_id
                self.input_images_refs.append(img_small)
                
                self.entry_message.insert(tk.END, " ")
                self.entry_message.focus_set()
        
        if self.emoji_window is not None and self.emoji_window.winfo_exists():
            self.emoji_window.destroy()
            self.emoji_window = None