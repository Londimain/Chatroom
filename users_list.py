import tkinter as tk
import database

class UsersList(tk.Frame):
    def __init__(self, parent, current_user_id, on_select=None):
        super().__init__(parent)
        self.current_user_id = current_user_id
        self.on_select = on_select

        # Используем шрифт Segoe UI (он ровный), убираем рамки (bd=0, highlightthickness=0)
        self.listbox = tk.Listbox(
            self, 
            font=("Segoe UI", 11), 
            activestyle='none',
            selectbackground='#505050',
            selectforeground='#ffffff',
            bd=0, 
            highlightthickness=0
        )
        # Добавляем 5 пикселей отступа внутри левой панели
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.listbox.bind('<Button-1>', self.on_click)

        self.refresh()

    def refresh(self):
        # Сохраняем текущее выделение
        selection = self.listbox.curselection()
        selected_id = None
        if selection:
            selected_index = selection[0]
            if hasattr(self, 'user_ids') and selected_index < len(self.user_ids):
                selected_id = self.user_ids[selected_index]

        self.listbox.delete(0, tk.END)
        users = database.get_all_users()
        self.user_ids = []
        for user in users:
            uid, username, display_name, is_online, is_admin, color = user
            display = display_name if display_name else username
            if is_admin:
                display += " ★"
            
            # ИСПОЛЬЗУЕМ ГЕОМЕТРИЧЕСКИЕ СИМВОЛЫ вместо эмодзи
            status = "●" if is_online else "○"
            
            # Добавляем 3 пробела в начале для имитации внутреннего отступа
            # Ровно один пробел перед статусом и три пробела после (для визуального разделения)
            # Добавляем 3 пробела в начале и 3 пробела после кружка для ровного выравнивания
            self.listbox.insert(tk.END, f"   {status}   {display}")
            self.user_ids.append(uid)

        # Восстанавливаем выделение
        if selected_id is not None and selected_id in self.user_ids:
            idx = self.user_ids.index(selected_id)
            self.listbox.selection_set(idx)
            self.listbox.activate(idx)

    def on_click(self, event):
        index = self.listbox.nearest(event.y)
        if index < self.listbox.size():
            bbox = self.listbox.bbox(index)
            if bbox and bbox[1] <= event.y <= bbox[1] + bbox[3]:
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(index)
                self.listbox.activate(index)
                uid = self.user_ids[index]
                if self.on_select:
                    self.on_select(uid)
                return

        self.listbox.selection_clear(0, tk.END)
        return "break"