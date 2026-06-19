import threading
from socket import *
from customtkinter import *
from PIL import Image
from tkinter import filedialog
import base64
import io
import os

class MainWindow(CTk):
    def __init__(self):
        super().__init__()
        self.geometry('400x300')
        self.title("LogiTalk")  
        self.label = None
        self.entry = None
        self.save_button = None  
        self.theme_button = None  

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        self.menu_frame = CTkFrame(self, width=0, height=300)
        self.menu_frame.grid_propagate(False)
        self.menu_frame.grid(row=0, column=0, rowspan=3, sticky="ns")
        self.menu_frame.grid_columnconfigure(0, weight=1)

        self.is_show_menu = False
        self.frame_width = 0
        self.menu_show_speed = 20  

        # кнопка для відкриття та закриття меню
        self.btn = CTkButton(self, text='▶️', command=self.show_menu, width=30)
        self.btn.grid(row=0, column=1, sticky="w")

        # main (елементи чату)
        self.chat_field = CTkScrollableFrame(self)  # змінили на скрол фрейм
        self.chat_field.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        self.chat_field.grid_columnconfigure(0, weight=1)  # даємо йому розширюватись у ширину

        # поле для введення тексту повідомлення
        self.message_entry = CTkEntry(self, placeholder_text='Введіть повідомлення:', height=40)
        self.message_entry.grid(row=2, column=1, sticky="ew", padx=(0, 95))

        # кнопку папки саджаємо в row=2, column=1 і притискаємо до правого краю ("e"), але з відступом від самого краю в 55px
        self.open_img_button = CTkButton(self, text="📂", width=40, height=40, command=self.open_image)
        self.open_img_button.grid(row=2, column=1, sticky="e", padx=(0, 55))

        # кнопку відправки саджаємо в row=2, column=1 і щільно притискаємо до самого правого краю ("e")
        self.send_button = CTkButton(self, text='>', width=50, height=40, command=self.send_message)
        self.send_button.grid(row=2, column=1, sticky="e")

        # мережева логіка
        self.username = 'Noname'  # ІДЕЯ ДЛЯ ТЕБЕ: Можна вписати сюди свій нік за замовчуванням
        self.current_theme = "Dark"  # ІДЕЯ ДЛЯ ТЕБЕ: Можна встановити початкову тему "Light"

        # спроба автоматичного підключення до сервера при старті
        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.connect(('localhost', 8080))
            hello = f"TEXT@{self.username}@[SYSTEM] {self.username} приєднався(лась) до чату!\n"
            self.sock.send(hello.encode('utf-8'))
            # запуск фонового потоку для безперервного прийому повідомлень
            threading.Thread(target=self.recv_message, daemon=True).start()
        except Exception as e:
            self.add_message(f"Не вдалося підключитися до сервера: {e}")

        # запуск циклу автоматичного підгону розмірів інтерфейсу
        self.adaptive_ui()

    # ФУНКЦІЇ ДЛЯ КЕРУВАННЯ МЕНЮ
    def show_menu(self):
        # перемикач стану меню: відкрити або закрити
        if self.is_show_menu:
            self.is_show_menu = False
            self.close_menu_animation()
        else:
            self.is_show_menu = True
            self.show_menu_animation()

    def show_menu_animation(self):
        # плавне висування меню та створення кнопок всередині нього
        if self.frame_width < 200:
            self.frame_width += self.menu_show_speed
            self.menu_frame.configure(width=self.frame_width)
            if self.frame_width >= 30:
                self.btn.configure(width=self.frame_width, text="◀️")

            # коли меню достатньо висунулось, створюємо внутрішні елементи
            if self.frame_width >= 40 and not self.label:
                self.label = CTkLabel(self.menu_frame, text='Імʼя')
                self.label.grid(row=0, column=0, pady=(30, 10), sticky="ew")
                self.entry = CTkEntry(self.menu_frame, placeholder_text="Новий нік...")  #
                self.entry.grid(row=1, column=0, padx=10, sticky="ew")

                self.save_button = CTkButton(self.menu_frame, text="Зберегти", command=self.save_name)  #
                self.save_button.grid(row=2, column=0, padx=10, pady=5, sticky="ew")  #

                self.theme_button = CTkButton(self.menu_frame, text="Тема: Темна", command=self.toggle_theme)  #
                self.theme_button.grid(row=3, column=0, padx=10, pady=(20, 10), sticky="ew")  #

            if self.is_show_menu:
                self.after(20, self.show_menu_animation)

    def close_menu_animation(self):
        # плавне ховання меню та повне видалення віджетів з пам'яті
        if self.frame_width > 0:
            self.frame_width -= self.menu_show_speed
            self.menu_frame.configure(width=self.frame_width)
            if self.frame_width >= 30:
                self.btn.configure(width=self.frame_width, text="▶️")
            else:
                self.btn.configure(width=30, text="▶️")

            # видаляємо віджети перед закриттям, щоб вони не зминалися потворно
            if self.frame_width <= 40 and self.label:
                self.label.destroy()
                self.entry.destroy()
                self.save_button.destroy()  #
                self.theme_button.destroy()  #
                self.label = None
                self.entry = None
                self.save_button = None  #
                self.theme_button = None  #

            if not self.is_show_menu:
                self.after(20, self.close_menu_animation)

    # ЛОГІКА КНОПОК МЕНЮ
    def save_name(self):
        # збереження нового нікнейму з текстового поля
        new_name = self.entry.get()
        if new_name:
            old_name = self.username
            self.username = new_name
            self.add_message(f"[Система]: Ви змінили нік з _{old_name}_ на _{self.username}_")
            self.entry.delete(0, END)

    def toggle_theme(self):
        # зміна кольорової теми додатка
        if self.current_theme == "Dark":
            set_appearance_mode("Light")
            self.current_theme = "Light"
            if self.theme_button:
                self.theme_button.configure(text="Тема: Світла")
        else:
            set_appearance_mode("Dark")
            self.current_theme = "Dark"
            if self.theme_button:
                self.theme_button.configure(text="Тема: Темна")

    # РОБОТА З ІНТЕРФЕЙСОМ
    def adaptive_ui(self):
        # динамічне вирахування ширини поля введення під розмір вікна, щоб кнопки не перекривали його
        send_btn_w = self.send_button.winfo_width()
        img_btn_w = self.open_img_button.winfo_width()

        # віднімаємо від загальної ширини вікна розмір меню та обох кнопок (плюс маленькі відступи)
        input_width = self.winfo_width() - self.frame_width - send_btn_w - img_btn_w - 15
        if input_width > 0:
            self.message_entry.configure(width=input_width)

        # оновлюємо відступ поля введення справа щоб текст не залазив под кнопки
        self.message_entry.grid(padx=(0, send_btn_w + img_btn_w + 5))
        self.after(50, self.adaptive_ui)

    def add_message(self, message, img=None):
        # додавання нового повідомлення або картинки в стрічку чату як окремого блока
        # ІДЕЯ ДЛЯ ТЕБЕ: Тут можна змінити колір плашки повідомлення (наприклад, "green", "blue", "grey20" тощо)
        message_frame = CTkFrame(self.chat_field, fg_color="grey")
        message_frame.pack(pady=5, padx=5, anchor="w")
        if message:
            CTkLabel(message_frame, text=message, text_color="white", justify="left").pack(padx=10, pady=5, anchor="w")
        if img:
            CTkLabel(message_frame, text="", image=img).pack(padx=10, pady=5, anchor="w")

    # МЕРЕЖЕВА ЛОГІКА ТА ВІДПРАВКА
    def send_message(self):
        # зчитування тексту з поля введення та відправка його на сервер
        message = self.message_entry.get()
        if message:
            self.add_message(f"{self.username}: {message}")  #
            data = f"TEXT@{self.username}@{message}\n"
            try:
                self.sock.sendall(data.encode())
            except Exception as e:
                self.add_message(f"[Система]: Помилка відправки: {e}.")  #
        self.message_entry.delete(0, END)

    def open_image(self):
        # відкриття провідника, кодування зображення в Base64 та його відправка
        file_name = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp")])
        if not file_name:
            return
        try:
            # читаємо картинку як бінарний файл і кодуємо в текст Base64
            with open(file_name, "rb") as f:
                raw = f.read()
            b64_data = base64.b64encode(raw).decode()
            short_name = os.path.basename(file_name)
            data = f"IMAGE@{self.username}@{short_name}@{b64_data}\n"
            try:
                if self.sock:  # перевіряємо чи сокет взагалі існує і підключений
                    self.sock.sendall(data.encode())
            except:
                pass

            # відображаємо надіслану картинку у власному вікні
            pil_img = Image.open(file_name)
            # ІДЕЯ ДЛЯ ТЕБЕ: Можна змінити розмір відображення картинки в чаті (наприклад, 200x200 чи 300x300)
            ctk_img = CTkImage(pil_img, size=(250, 250))
            self.add_message(f"{self.username} надіслав зображення:", img=ctk_img)
        except Exception as e:
            self.add_message(f"Не вдалось надіслати зображення: {e}")

    def recv_message(self):
        # постійне фонове прослуховування сервера та збір отриманих байтів у буфер
        buffer = ""
        while True:
            try:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                buffer += chunk.decode()
                # якщо в буфері є символ переносу рядка, значить повідомлення прийшло повністю
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    self.handle_line(line.strip())
            except:
                break
        self.sock.close()

    def handle_line(self, line):
        # розбір отриманого рядка та виведення в чат
        if not line:
            return
        parts = line.split("@", 3)
        msg_type = parts[0]

        # обробка звичайного тексту
        if msg_type == "TEXT":
            if len(parts) >= 3:
                author = parts[1]
                message = parts[2]
                if author != self.username:  # свої повідомлення ми вже додали при відправці
                    self.add_message(f"{author}: {message}")

        # обробка отриманого зображення
        elif msg_type == "IMAGE":
            if len(parts) >= 4:
                author = parts[1]
                filename = parts[2]
                b64_img = parts[3]  #
                if author != self.username:
                    try:
                        # декодуємо текст Base64 назад у картинку
                        img_data = base64.b64decode(b64_img)
                        pil_img = Image.open(io.BytesIO(img_data))
                        ctk_img = CTkImage(pil_img, size=(250, 250))
                        # ІДЕЯ ДЛЯ ТЕБЕ: Можна змінити текст системного повідомлення (наприклад, "{author} поділився фото:")
                        self.add_message(f"{author} надіслав зображення: {filename}", img=ctk_img)
                    except Exception as e:
                        self.add_message(f"Помилка відображення зображення від {author}: {e}.")
        else:
            self.add_message(line)

# ЗАПУСК ПРОГРАМИ
win = MainWindow()
win.mainloop()
