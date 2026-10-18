import utils
import tkinter as tk
from tkinter import ttk
import database
from chat_panel import ChatPanel
from admin_users_view import AdminUsersPanel
from forum_view import ForumPanel
from settings_view import SettingsPanel
from statistics_view import StatisticsPanel
from about_view import AboutPanel
import os

class MainApp(tk.Tk):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.title("Чат")
        utils.center_window(self, 1000, 650)
        self.minsize(800, 500)

        chat_ico = utils.resource_path('ico/chat.ico')
        if os.path.exists(chat_ico):
            self.iconbitmap(chat_ico)

        self.user_data = database.get_user(user_id)
        self.current_theme = self.user_data.get('theme', 'light')

        # Загружаем иконки
        self.icons = {}
        icon_names = ['chat', 'users', 'forum', 'settings', 'stats', 'chatabout']
        for name in icon_names:
            path = utils.resource_path(f'ico/{name}.png')
            if os.path.exists(path):
                try:
                    self.icons[name] = tk.PhotoImage(file=path)
                except:
                    self.icons[name] = None
            else:
                self.icons[name] = None

        # Верхняя панель
        self.top_frame = tk.Frame(self, bg='#e0e0e0')
        self.top_frame.pack(fill=tk.X)
        self.label_title = tk.Label(self.top_frame, text=f"Чат - {self.user_data['display_name']}",
                                    font=("Arial", 14, "bold"), bg=self.top_frame['bg'])
        self.label_title.pack(side=tk.LEFT, padx=10, pady=5)
        if self.user_data['is_admin']:
            tk.Label(self.top_frame, text="(Админ)", font=("Arial", 10, "italic"),
                     bg=self.top_frame['bg']).pack(side=tk.LEFT, padx=5)

        # Навигация
        self.nav_frame = tk.Frame(self, bg='#d0d0d0')
        self.nav_frame.pack(fill=tk.X)

        self.nav_buttons = []

        # Добавляем пробелы для центрирования текста в кнопках
        btn_chat = utils.create_button(
            self.nav_frame, self.icons.get('chat'), "       Чат",
            command=lambda: self.show_panel('chat'), width=120, height=35, bg='#e0e0e0'
        )
        self.nav_buttons.append(btn_chat)

        if self.user_data['is_admin']:
            btn_users = utils.create_button(
                self.nav_frame, self.icons.get('users'), "Пользователи",
                command=lambda: self.show_panel('users'), width=120, height=35, bg='#e0e0e0'
            )
            self.nav_buttons.append(btn_users)

        btn_forum = utils.create_button(
            self.nav_frame, self.icons.get('forum'), "    Форум  ",
            command=lambda: self.show_panel('forum'), width=120, height=35, bg='#e0e0e0'
        )
        self.nav_buttons.append(btn_forum)

        btn_settings = utils.create_button(
            self.nav_frame, self.icons.get('settings'), "  Настройки",
            command=lambda: self.show_panel('settings'), width=120, height=35, bg='#e0e0e0'
        )
        self.nav_buttons.append(btn_settings)

        if self.user_data['is_admin']:
            btn_stats = utils.create_button(
                self.nav_frame, self.icons.get('stats'), "  Статистика",
                command=lambda: self.show_panel('stats'), width=120, height=35, bg='#e0e0e0'
            )
            self.nav_buttons.append(btn_stats)

        btn_about = utils.create_button(
            self.nav_frame, self.icons.get('chatabout'), "О программе",
            command=lambda: self.show_panel('about'), width=120, height=35, bg='#e0e0e0'
        )
        self.nav_buttons.append(btn_about)

        self.main_container = tk.Frame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        self.chat_panel = None
        self.admin_users_panel = None
        self.forum_panel = None
        self.settings_panel = None
        self.stats_panel = None
        self.about_panel = None
        self.current_panel = None

        self.create_panels()
        self.apply_theme_to_all(self.current_theme)
        self.show_panel('chat')

        self.after(3000, self.update_loop)

        self.profile_window = None
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_panels(self):
        try:
            self.chat_panel = ChatPanel(self.main_container, self.user_id)
        except Exception as e:
            print(f"Ошибка создания чата: {e}")
            self.chat_panel = None

        try:
            self.admin_users_panel = AdminUsersPanel(self.main_container, self.user_id)
        except Exception as e:
            print(f"Ошибка создания админ-панели: {e}")
            self.admin_users_panel = None

        try:
            self.forum_panel = ForumPanel(self.main_container, self.user_id)
        except Exception as e:
            print(f"Ошибка создания форума: {e}")
            self.forum_panel = None

        try:
            self.settings_panel = SettingsPanel(self.main_container, self.user_id)
        except Exception as e:
            print(f"Ошибка создания настроек: {e}")
            self.settings_panel = None

        try:
            self.stats_panel = StatisticsPanel(self.main_container, self.user_id)
        except Exception as e:
            print(f"Ошибка создания статистики: {e}")
            self.stats_panel = None

        try:
            self.about_panel = AboutPanel(self.main_container, self.user_id)
        except Exception as e:
            print(f"Ошибка создания панели 'О программе': {e}")
            self.about_panel = None

    def show_panel(self, name):
        for panel in [self.chat_panel, self.admin_users_panel, self.forum_panel,
                      self.settings_panel, self.stats_panel, self.about_panel]:
            if panel is not None:
                try:
                    panel.pack_forget()
                except:
                    pass

        if name == 'chat' and self.chat_panel is not None:
            self.chat_panel.pack(fill=tk.BOTH, expand=True)
            self.current_panel = self.chat_panel
        elif name == 'users' and self.admin_users_panel is not None:
            self.admin_users_panel.pack(fill=tk.BOTH, expand=True)
            self.current_panel = self.admin_users_panel
        elif name == 'forum' and self.forum_panel is not None:
            self.forum_panel.pack(fill=tk.BOTH, expand=True)
            self.current_panel = self.forum_panel
        elif name == 'settings' and self.settings_panel is not None:
            self.settings_panel.pack(fill=tk.BOTH, expand=True)
            self.current_panel = self.settings_panel
        elif name == 'stats' and self.stats_panel is not None:
            self.stats_panel.pack(fill=tk.BOTH, expand=True)
            self.current_panel = self.stats_panel
        elif name == 'about' and self.about_panel is not None:
            self.about_panel.pack(fill=tk.BOTH, expand=True)
            self.current_panel = self.about_panel

    def open_profile(self, viewed_user_id):
        if self.profile_window is not None and self.profile_window.winfo_exists():
            self.profile_window.lift()
            self.profile_window.focus()
            return
        from profile_view import ProfileView
        self.profile_window = ProfileView(self, self.user_id, viewed_user_id)
        self.profile_window.protocol("WM_DELETE_WINDOW", self._close_profile_window)

    def _close_profile_window(self):
        if self.profile_window is not None:
            self.profile_window.destroy()
            self.profile_window = None

    def update_loop(self):
        if self.current_panel is not None and hasattr(self.current_panel, 'refresh'):
            if self.current_panel != self.settings_panel:
                try:
                    self.current_panel.refresh()
                except Exception as e:
                    print(f"Ошибка обновления панели: {e}")
        self.after(3000, self.update_loop)

    def on_close(self):
        database.set_online_status(self.user_id, False)
        database.update_last_seen(self.user_id)
        self.destroy()

    def apply_theme_to_all(self, theme_name):
        # Применяем тему ко всему главному окну рекурсивно (включая все панели)
        utils.apply_theme(self, theme_name)
        
        # Дополнительно применяем специфичные стили для панелей с таблицами (Treeview)
        if self.stats_panel is not None and hasattr(self.stats_panel, 'apply_theme'):
            self.stats_panel.apply_theme(theme_name)
        if self.forum_panel is not None and hasattr(self.forum_panel, 'apply_theme'):
            self.forum_panel.apply_theme(theme_name)
        if self.admin_users_panel is not None and hasattr(self.admin_users_panel, 'apply_theme'):
            self.admin_users_panel.apply_theme(theme_name)
            
        self.current_theme = theme_name