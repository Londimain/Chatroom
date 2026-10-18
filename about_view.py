import tkinter as tk
from tkinter import ttk
import utils
import webbrowser
import os

class AboutPanel(tk.Frame):
    def __init__(self, parent, user_id):
        super().__init__(parent)
        self.user_id = user_id

        tk.Label(self, text="О программе", font=("Arial", 16, "bold")).pack(pady=10)

        # Основной текст
        text_frame = tk.Frame(self)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        info_text = tk.Text(text_frame, wrap=tk.WORD, font=("Arial", 11), height=20, bd=0, highlightthickness=0)
        info_text.pack(fill=tk.BOTH, expand=True)

        # Содержимое
        content = """
        Добро пожаловать в Чат!

        Это многофункциональное приложение для общения и обмена файлами, 
        разработанное с использованием современного интерфейса.

        🔹 Основные возможности:

        1. Чат
           - Общение в общем чате в реальном времени (автообновление каждые 3 секунды).
           - Использование собственных цветных смайликов (из папки Smile).
           - Звуковые уведомления о новых сообщениях (свой звук для каждого пользователя).
           - Отображение ника пользователя с выбранным цветом.
           - Список всех пользователей с индикацией онлайн/офлайн.
           - Администратор может полностью очистить историю чата.

        2. Пользователи (только для администратора)
           - Удобная таблица со всей информацией: ID, логин, ник, статус, роль и дата регистрации.
           - Быстрое открытие профиля любого пользователя.
           - Возможность выдать или забрать права администратора.
           - Полное удаление пользователя (вместе с его файлами и сообщениями).

        3. Форум
           - Создание категорий и страниц.
           - Обмен сообщениями внутри страниц.
           - Загрузка и скачивание файлов (с ограничением по объёму).
           - Редактирование и удаление своих категорий/страниц.
           - Очистка всех постов на странице и удаление прикреплённых файлов (для создателя страницы и админа).
           - Подсветка своих элементов (синим цветом).

        4. Настройки
           - Красивый и удобный интерфейс с разделением на блоки.
           - Выбор цвета ника (сохраняется в БД).
           - Смена темы оформления (Светлая, Тёмная, Синяя).
           - Включение/отключение звука и выбор своего звукового файла из выпадающего списка (с кнопкой «Тест»).

        5. Статистика (только для администратора)
           - Просмотр объёма загруженных файлов по каждому пользователю.
           - Детальный список файлов с указанием категории и страницы.
           - Возможность открыть или удалить любой файл прямо из окна статистики.

        6. Профиль пользователя
           - Просмотр информации (ФИО, должность, телефон, дата регистрации, статус).
           - Загрузка и удаление аватарки.
           - Редактирование своих данных (или чужих — для администратора).
           - Удаление пользователя администратором прямо из окна редактирования.

        🔹 Краткое руководство:

        - Войдите в систему под своим логином и паролем.
        - Для смены ника, цвета или звука перейдите в раздел «Настройки».
        - В чате введите сообщение, при необходимости добавьте смайлы, и нажмите Enter.
        - Чтобы открыть профиль пользователя, кликните на его имя в списке слева.
        - В форуме создавайте категории и страницы, общайтесь и обменивайтесь файлами.
        - Администратор имеет полный доступ к управлению пользователями и статистике.
        """

        info_text.insert("1.0", content)
        info_text.config(state=tk.DISABLED)

        # --- Кнопки (стандартные tk.Button) ---
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=15)

        # Загружаем иконки
        icons = {}
        icon_names = ['github', 'discord', 'telegram']
        for name in icon_names:
            path = utils.resource_path(f'ico/{name}.png')
            if os.path.exists(path):
                try:
                    icons[name] = tk.PhotoImage(file=path)
                except:
                    icons[name] = None
            else:
                icons[name] = None

        # Общая ширина кнопок
        btn_width = 110  # в символах

        # GitHub
        btn_github = tk.Button(btn_frame, text="    GitHub", image=icons.get('github'),
                               compound=tk.LEFT, bd=3, relief='flat',
                               width=btn_width, anchor='w', padx=5,
                               command=lambda: webbrowser.open('https://github.com/Londimain/Chatroom'))
        btn_github.pack(side=tk.LEFT, padx=10, expand=True)

        # Discord
        btn_discord = tk.Button(btn_frame, text="    Discord", image=icons.get('discord'),
                                compound=tk.LEFT, bd=3, relief='flat',
                                width=btn_width, anchor='w', padx=5,
                                command=lambda: webbrowser.open('https://discordapp.com/users/935146921813745725'))
        btn_discord.pack(side=tk.LEFT, padx=10, expand=True)

        # Telegram
        btn_telegram = tk.Button(btn_frame, text="   Telegram", image=icons.get('telegram'),
                                 compound=tk.LEFT, bd=3, relief='flat',
                                 width=btn_width, anchor='w', padx=5,
                                 command=lambda: webbrowser.open('https://t.me/GodiNesF'))
        btn_telegram.pack(side=tk.LEFT, padx=10, expand=True)

        # Сохраняем иконки, чтобы они не удалялись
        self.btn_icons = icons