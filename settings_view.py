import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
import database
import utils
import os

class SettingsPanel(tk.Frame):
    def __init__(self, parent, user_id):
        super().__init__(parent)
        self.user_id = user_id
        self.user_data = database.get_user(user_id)

        tk.Label(self, text="Настройки", font=("Arial", 18, "bold")).pack(pady=(15, 10))

        # ==========================================
        # БЛОК 1: ВНЕШНИЙ ВИД
        # ==========================================
        frame_appearance = tk.LabelFrame(self, text=" Внешний вид ", font=("Arial", 11, "bold"), padx=15, pady=15)
        frame_appearance.pack(fill=tk.X, padx=20, pady=10)

        # -- Цвет ника --
        row_color = tk.Frame(frame_appearance)
        row_color.pack(fill=tk.X, pady=5, anchor='w')
        
        tk.Label(row_color, text="Цвет ника:", font=("Arial", 11)).pack(side=tk.LEFT)
        
        # Квадратик цвета (кликабельный)
        self.color_preview = tk.Label(
            row_color, 
            text="  ", 
            bg=self.user_data.get('nickname_color', '#000000'), 
            width=4, 
            name='color_preview',
            bd=2,
            relief="solid",
            cursor="hand2" 
        )
        self.color_preview.pack(side=tk.LEFT, padx=10)
        self.color_preview.bind("<Button-1>", lambda e: self.choose_color())
        
        tk.Button(row_color, text="Выбрать цвет...", command=self.choose_color).pack(side=tk.LEFT, padx=5)

        # -- Тема --
        row_theme = tk.Frame(frame_appearance)
        row_theme.pack(fill=tk.X, pady=(15, 5), anchor='w')
        
        tk.Label(row_theme, text="Тема оформления:", font=("Arial", 11)).pack(side=tk.LEFT, padx=(0, 10))
        
        self.theme_var = tk.StringVar(value=self.user_data.get('theme', 'light'))
        
        # Используем ttk.Radiobutton для корректного отображения в темах
        ttk.Radiobutton(row_theme, text="Светлая", variable=self.theme_var, value="light").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(row_theme, text="Тёмная", variable=self.theme_var, value="dark").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(row_theme, text="Синяя", variable=self.theme_var, value="blue").pack(side=tk.LEFT, padx=5)

        # ==========================================
        # БЛОК 2: УВЕДОМЛЕНИЯ
        # ==========================================
        frame_sound = tk.LabelFrame(self, text=" Звуковые уведомления ", font=("Arial", 11, "bold"), padx=15, pady=15)
        frame_sound.pack(fill=tk.X, padx=20, pady=10)

        # -- Чекбокс включения --
        self.sound_enabled_var = tk.IntVar(value=self.user_data.get('sound_enabled', 1))
        
        # Используем ttk.Checkbutton для корректного отображения
        chk = ttk.Checkbutton(
            frame_sound, 
            text="Включить звук при новом сообщении", 
            variable=self.sound_enabled_var,
            command=self.toggle_sound_controls 
        )
        chk.pack(anchor='w', pady=(0, 10))

        # -- Выбор звука и тест --
        row_sound_select = tk.Frame(frame_sound)
        row_sound_select.pack(fill=tk.X, anchor='w')
        
        tk.Label(row_sound_select, text="Звук:", font=("Arial", 11)).pack(side=tk.LEFT, padx=(0, 10))
        
        self.sound_files = self.scan_sounds()
        self.sound_var = tk.StringVar()
        
        self.sound_combo = ttk.Combobox(row_sound_select, textvariable=self.sound_var, values=self.sound_files, state='readonly', width=30)
        self.sound_combo.pack(side=tk.LEFT, padx=5)
        
        current_sound = self.user_data.get('sound_path', '')
        if current_sound in self.sound_files:
            self.sound_var.set(current_sound)
        elif self.sound_files:
            self.sound_var.set(self.sound_files[0])
            
        self.btn_test = tk.Button(row_sound_select, text="Тест", command=self.test_sound)
        self.btn_test.pack(side=tk.LEFT, padx=10)

        self.toggle_sound_controls()

        # ==========================================
        # КНОПКА СОХРАНЕНИЯ
        # ==========================================
        btn_save = tk.Button(
            self, 
            text="Применить настройки", 
            font=("Arial", 12, "bold"), 
            padx=20, 
            pady=8, 
            bg="#1976D2",            
            fg="white",              
            activebackground="#1565C0", 
            activeforeground="white",
            bd=1,                    
            relief="solid",          
            highlightthickness=0,    
            name='btn_save_settings', 
            command=self.apply_settings
        )
        btn_save.pack(pady=25)

    def toggle_sound_controls(self):
        """Блокирует или разблокирует выбор звука в зависимости от чекбокса."""
        if self.sound_enabled_var.get() == 1:
            self.sound_combo.config(state='readonly')
            self.btn_test.config(state=tk.NORMAL)
        else:
            self.sound_combo.config(state='disabled')
            self.btn_test.config(state=tk.DISABLED)

    def scan_sounds(self):
        """Ищет .wav файлы в папке sounds."""
        sounds_dir = utils.resource_path('sounds')
        if not os.path.exists(sounds_dir):
            os.makedirs(sounds_dir, exist_ok=True)
            return []
        
        files = [f for f in os.listdir(sounds_dir) if f.lower().endswith('.wav')]
        return sorted(files)

    def choose_color(self):
        color = colorchooser.askcolor(title="Выберите цвет ника", color=self.color_preview.cget('bg'))[1]
        if color:
            self.color_preview.config(bg=color)

    def test_sound(self):
        if self.sound_enabled_var.get() == 0:
            return
            
        utils.play_sound(self.sound_var.get())

    def apply_settings(self):
        color = self.color_preview.cget('bg')
        theme = self.theme_var.get()
        sound_enabled = self.sound_enabled_var.get()
        sound_file = self.sound_var.get()

        database.update_nickname_color(self.user_id, color)
        database.update_theme(self.user_id, theme)
        database.update_sound_settings(self.user_id, sound_enabled, sound_file)

        messagebox.showinfo("Успех", "Настройки успешно сохранены!")
        self.user_data = database.get_user(self.user_id)

        parent = self.winfo_toplevel()
        if hasattr(parent, 'apply_theme_to_all'):
            parent.apply_theme_to_all(theme)
            
        self.color_preview.config(bg=color)

        if hasattr(parent, 'chat_panel') and parent.chat_panel is not None:
            parent.chat_panel.refresh()

        self.refresh()

    def refresh(self):
        self.user_data = database.get_user(self.user_id)
        self.theme_var.set(self.user_data.get('theme', 'light'))
        
        self.sound_files = self.scan_sounds()
        self.sound_combo['values'] = self.sound_files
        
        self.sound_enabled_var.set(self.user_data.get('sound_enabled', 1))
        
        current_sound = self.user_data.get('sound_path', '')
        if current_sound in self.sound_files:
            self.sound_var.set(current_sound)
            
        self.toggle_sound_controls()