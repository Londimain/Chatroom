import database
from auth import LoginWindow

if __name__ == "__main__":
    # Инициализируем БД (создаёт таблицы и админа)
    database.init_db()
    # Запускаем окно входа
    app = LoginWindow()
    app.mainloop()