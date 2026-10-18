import os
import hashlib
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk
import webbrowser
import sys
import winsound

def resource_path(relative_path):
    """Возвращает абсолютный путь к ресурсу."""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def scale_image(image_path, max_size=(150, 150)):
    if not image_path or not os.path.exists(image_path):
        return None
    try:
        img = Image.open(image_path)
        img.thumbnail(max_size, Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except:
        return None

def format_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024*1024:
        return f"{size_bytes/1024:.2f} KB"
    elif size_bytes < 1024*1024*1024:
        return f"{size_bytes/(1024*1024):.2f} MB"
    else:
        return f"{size_bytes/(1024*1024*1024):.2f} GB"

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def get_app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_upload_path(subdir=''):
    base = os.path.join(get_app_dir(), 'uploads')
    ensure_dir(base)
    if subdir:
        full = os.path.join(base, subdir)
        ensure_dir(full)
        return full
    return base

def set_window_icon(window):
    ico_path = resource_path('ico/chat.ico')
    if os.path.exists(ico_path):
        try:
            window.iconbitmap(ico_path)
        except:
            pass

def create_button(parent, icon, text, command=None, url=None, width=120, height=35, bg='#e0e0e0', fg='black'):
    """Создаёт стандартную кнопку с эффектами."""
    btn = tk.Button(parent, text=text, image=icon, compound=tk.LEFT,
                    command=command if command else (lambda: webbrowser.open(url) if url else None),
                    bg=bg, fg=fg, font=("Arial", 10),
                    bd=1, relief='raised', width=width, height=height,
                    anchor='w', padx=5)
    btn.pack(side=tk.LEFT, padx=2, pady=2)

    # Сохраняем цвета
    btn._bg = bg
    btn._fg = fg
    btn._active_bg = '#d0d0d0' # Цвет при наведении (будет меняться темой)

    def on_enter(e):
        btn.config(bg=btn._active_bg)
    def on_leave(e):
        btn.config(bg=btn._bg)
    def on_press(e):
        btn.config(relief='sunken', bg=btn._active_bg)
    def on_release(e):
        btn.config(relief='raised', bg=btn._active_bg)

    btn.bind('<Enter>', on_enter)
    btn.bind('<Leave>', on_leave)
    btn.bind('<ButtonPress-1>', on_press)
    btn.bind('<ButtonRelease-1>', on_release)

    btn._button_data = {'bg': bg, 'fg': fg}
    return btn

def apply_theme(widget, theme_name):
    """Рекурсивно применяет цветовую тему ко всем виджетам."""
    # Пропускаем кастомные виджеты
    if hasattr(widget, 'winfo_name'):
        w_name = widget.winfo_name()
        if w_name in ('color_preview', 'btn_save_settings'):
            return

    themes = {
        'light': {'bg': '#f0f0f0', 'button_bg': '#e0e0e0', 'entry_bg': '#ffffff', 'listbox_bg': '#ffffff', 'fg': '#000000'},
        'dark': {'bg': '#2b2b2b', 'button_bg': '#3c3c3c', 'entry_bg': '#3c3c3c', 'listbox_bg': '#3c3c3c', 'fg': '#ffffff'},
        'blue': {'bg': '#d9e4f5', 'button_bg': '#b0c4de', 'entry_bg': '#ffffff', 'listbox_bg': '#ffffff', 'fg': '#000000'}
    }
    theme = themes.get(theme_name, themes['light'])

    # Кнопки навигации (созданные через create_button)
    if hasattr(widget, '_button_data'):
        widget.config(bg=theme['button_bg'], fg=theme['fg'])
        widget._bg = theme['button_bg']
        widget._fg = theme['fg']
        widget._button_data['bg'] = theme['button_bg']
        widget._button_data['fg'] = theme['fg']
        
        # ИСПРАВЛЕНИЕ: Меняем цвет при наведении в зависимости от темы
        if theme_name == 'dark':
            widget._active_bg = '#505050'  # Темно-серый для темной темы (чтобы белый текст читался)
        elif theme_name == 'blue':
            widget._active_bg = '#90a4c4'  # Темно-синий для синей темы
        else:
            widget._active_bg = '#d0d0d0'  # Светло-серый для светлой
            
        widget.config(bg=widget._bg) # Принудительно обновляем фон
        return

    # Обработка стандартных виджетов Tkinter
    if isinstance(widget, tk.LabelFrame):
        try: widget.configure(bg=theme['bg'], fg=theme['fg'])
        except: pass
    elif isinstance(widget, (tk.Label, tk.Radiobutton, tk.Checkbutton)):
        try:
            widget.configure(bg=theme['bg'], fg=theme['fg'])
            if hasattr(widget, 'selectcolor'):
                widget.configure(selectcolor=theme['entry_bg'])
        except: pass
    elif isinstance(widget, tk.Frame):
        try: widget.configure(bg=theme['bg'])
        except: pass
    elif isinstance(widget, tk.Button):
        try: widget.configure(bg=theme['button_bg'], fg=theme['fg'])
        except: pass
    elif isinstance(widget, (tk.Entry, tk.Text)):
        try: widget.configure(bg=theme['entry_bg'], fg=theme['fg'])
        except: pass
    elif isinstance(widget, tk.Listbox):
        try: 
            widget.configure(
                bg=theme['listbox_bg'], 
                fg=theme['fg'],
                selectbackground=theme['button_bg'],
                selectforeground=theme['fg']
            )
        except: pass
        
    # Обработка виджетов ttk (тема clam)
    elif isinstance(widget, (ttk.Radiobutton, ttk.Checkbutton)):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TRadiobutton", background=theme['bg'], foreground=theme['fg'])
        style.map("TRadiobutton", background=[('active', theme['bg'])], foreground=[('active', theme['fg'])])
        style.configure("TCheckbutton", background=theme['bg'], foreground=theme['fg'])
        style.map("TCheckbutton", background=[('active', theme['bg'])], foreground=[('active', theme['fg'])])
        
        # Убираем пунктир фокуса
        style.layout('TCheckbutton', [
            ('Checkbutton.padding', {'sticky': 'nswe', 'children': [
                ('Checkbutton.indicator', {'side': 'left', 'sticky': ''}),
                ('Checkbutton.label', {'side': 'left', 'sticky': ''})
            ]})
        ])
        style.layout('TRadiobutton', [
            ('Radiobutton.padding', {'sticky': 'nswe', 'children': [
                ('Radiobutton.indicator', {'side': 'left', 'sticky': ''}),
                ('Radiobutton.label', {'side': 'left', 'sticky': ''})
            ]})
        ])
        
    elif isinstance(widget, ttk.Combobox):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TCombobox", fieldbackground=theme['entry_bg'], background=theme['button_bg'], foreground=theme['fg'])
    elif isinstance(widget, ttk.Treeview):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview.Heading", background=theme['button_bg'], foreground="black", relief="raised")
        style.configure("Treeview", background=theme['bg'], fieldbackground=theme['bg'], foreground=theme['fg'])
    else:
        try: widget.configure(bg=theme['bg'])
        except: pass

    # Рекурсивный обход
    for child in widget.winfo_children():
        apply_theme(child, theme_name)
        
def center_window(window, width, height):
    """Центрирует окно на экране."""
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = int((screen_width / 2) - (width / 2))
    y = int((screen_height / 2) - (height / 2))
    window.geometry(f"{width}x{height}+{x}+{y}")
    
def play_sound(sound_filename=None):
    """Проигрывает звук из папки sounds."""
    if sound_filename:
        sound_path = resource_path(f'sounds/{sound_filename}')
        if os.path.exists(sound_path):
            try:
                winsound.PlaySound(sound_path, winsound.SND_ASYNC | winsound.SND_FILENAME)
                return
            except Exception:
                pass
    
    winsound.MessageBeep(winsound.MB_ICONASTERISK)