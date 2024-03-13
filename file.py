import sqlite3
import datetime
import os
def adapt_datetime_iso(val):
    return val.isoformat()
sqlite3.register_adapter(datetime.datetime, adapt_datetime_iso)
class Library:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY,
                            username TEXT UNIQUE,
                            password TEXT)''')
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS books (
                            id INTEGER PRIMARY KEY,
                            title TEXT,
                            author TEXT,
                            count INTEGER,
                            UNIQUE(title, author))''')
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS loans (
                            id INTEGER PRIMARY KEY,
                            user_id INTEGER,
                            book_id INTEGER,
                            return_date DATETIME,
                            FOREIGN KEY(user_id) REFERENCES users(id),
                            FOREIGN KEY(book_id) REFERENCES books(id))''')
        self.conn.commit()

    def get_all_books(self): 
        self.cursor.execute("SELECT * FROM books")
        return self.cursor.fetchall()
        
    def print_all_books(self):
        books = self.get_all_books()
        if len(books) < 1:
            return False
        print()
        print("Доступные книги:")
        print("ID | Название книги | Автор книги | Количество")
        for i in books:
            print(i)
        return True
        
        
    def get_all_loans(self, user_id): 
        print(user_id)
        self.cursor.execute("SELECT loans.id, books.title, loans.return_date FROM loans JOIN books ON loans.book_id = books.id WHERE user_id=?", (user_id,))
        return self.cursor.fetchall()
        
    def print_all_loans(self, user_id):
        print(user_id)
        books = self.get_all_loans(user_id)
        if len(books) < 1:
            return False
        print()
        print("Доступные книги:")
        print("ID | Название книги | Дата выдачи | Просрочено")
        for i in books:
            print(i[0],"|", i[1],"|", (datetime.datetime.now(datetime.timezone.utc) - (datetime.datetime.fromisoformat(i[2]) - datetime.timedelta(days=return_date_days))),"|", datetime.datetime.fromisoformat(i[2]) < datetime.datetime.now(datetime.timezone.utc))
        return True

    def register_user(self, username, password):
        try:
            self.cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            self.conn.commit()
            print("Пользователь", username, "успешно зарегистрирован!")
        except sqlite3.IntegrityError:
            print("Ошибка создания.")

    def login_user(self, username, password):
        self.cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = self.cursor.fetchone()
        if user:
            print("Вы успешно зашли как", username)
            return user[0]  # Return user id
        else:
            print("Неправильно введённые данные!")
            return None

    def add_book(self, title, author, count):
        try:
            self.cursor.execute("INSERT INTO books (title, author, count) VALUES (?, ?, ?)", (title, author, count))
            self.conn.commit()
            print("Книга была успешно добавлена!")
        except sqlite3.IntegrityError:
            print("Книга с данным названием уже существует в базе данных!")

    def lend_book(self, user_id, book_id, return_date):
        try:
            self.cursor.execute("SELECT count FROM books WHERE id=?", (book_id))
            book_count = self.cursor.fetchone()
            if book_count[0] < 1:
                print("Невозможно выдать книгу - нет в наличии!")
                return
            self.cursor.execute("INSERT INTO loans (user_id, book_id, return_date) VALUES (?, ?, ?)", (user_id, book_id, return_date))
            self.cursor.execute("UPDATE books SET count = count - 1 WHERE id=?", (book_id))
            self.conn.commit()
            print("Книга была успешно выдана!")
        except sqlite3.IntegrityError:
            print("Книга/пользователь не найдены!")

    def return_book(self, loan_id):
        self.cursor.execute("SELECT * FROM loans WHERE id=?", (loan_id,))
        loan = self.cursor.fetchone()
        if datetime.datetime.fromisoformat(loan[3]) < datetime.datetime.now(datetime.timezone.utc):
            a = input("Обнаружена просрочка за книгу. Подтвердите оплату просрочки перед продолжением:")
        self.cursor.execute("DELETE FROM loans WHERE id=?", (loan_id,))
        self.cursor.execute("UPDATE books SET count = count + 1 WHERE id=?", (loan[2],))
        self.conn.commit()
        if self.cursor.rowcount > 0:
            print("Данная книга была успешно возвращена!")
        else:
            print("Вы не брали эту книгу.")
            
    def get_book_info(self, book_id):
        self.cursor.execute("SELECT * FROM books WHERE id=?", (book_id))
        book = self.cursor.fetchone()
        if book:
            return book
        else:
            return False

    def check_fines(self, user_id):
        self.cursor.execute("SELECT books.title, loans.return_date FROM books INNER JOIN loans ON books.id = loans.book_id WHERE loans.user_id=?", (user_id,))
        books = self.cursor.fetchall()
        print("------------------")
        total_fine = 0
        if len(books) == 0:
            print("У вас нет не возвращённых книг!")
            return
        for book, return_date in books:
            print(f"Вы взяли книгу '{book}'", (datetime.datetime.now(datetime.timezone.utc) - (datetime.datetime.fromisoformat(return_date) - datetime.timedelta(days=return_date_days))).days, "дня/дней назад")
            if datetime.datetime.fromisoformat(return_date) < datetime.datetime.now(datetime.timezone.utc):
                fine_days = (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(return_date)).days
                fine = fine_days * fine_per_day
                if fine > 0:
                    print("Просрочка за книгу", book, "составляет", fine, "рублей")
                total_fine += fine
            elif datetime.datetime.fromisoformat(return_date) >= datetime.datetime.now(datetime.timezone.utc):
                print("У вас осталось ~", (datetime.datetime.fromisoformat(return_date) - datetime.datetime.now(datetime.timezone.utc)).days + 1, "дня/дней, чтобы вернуть эту книгу.\nВ противном случае - будет применён штраф в размере",fine_per_day,"рублей за каждый день просрочки!")
            print("------------------")
        if total_fine > 0:
            print()
            print(f"Ваша общая просрочка: {total_fine} рублей")
        else:
            print("Нет просрочки.")
return_date_days = 14
fine_per_day = 10
def main():
    library = Library("library.db")
    while True:
        try:
            print("1. Войти")
            print("2. Зарегистрироваться")
            print("3. Выйти")
            choice = input("Выберите действие: ")
            
            if choice == "1":
                username = input("Введите логин: ")
                password = input("Введите пароль: ")
                user_id = library.login_user(username, password)
                if user_id:
                    while True:                    
                        print("1. Взять книгу")
                        print("2. Вернуть книгу")
                        print("3. Проверить статус взятых книг")
                        print("4. Добавить книгу в библиотеку")
                        print("5. Вернуться в меню")
                        user_choice = input("Выберите действие: ")
                        
                        if user_choice == "1":
                            check = library.print_all_books()
                            if not check:
                                print("В базе данных не обнаружено книг!")
                                break
                            book_id = input("Введите идентификатор книги (BOOK_ID), чтобы взять её: ")
                            book_count = input("В библиотеке есть возможность взять несколько книг одного типа\nОбращаем ваше внимание, что если количество книг, которое вы введёте, будет больше доступного количества в нашей базе - вам будут выданы лишь все доступные\nВведите количество (оставьте пустым для одной книги):")
                            if book_count == "":
                                book_count = 1
                            book_count = int(book_count)
                            book = library.get_book_info(book_id)
                            if book:
                                return_date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=return_date_days)
                                for i in range(book_count):
                                    library.lend_book(user_id, book_id, return_date)
                            else:
                                print("Книга с идентификатором (BOOK_ID)", book_id, "не была найдена!")           
                        elif user_choice == "2":
                            check = library.print_all_loans(int(user_id))
                            if not check:
                                print("У вас нет невозвращённых книг!")
                                break
                            loan_id = input("Введите идентификатор записи (LOAN_ID), чтобы вернуть соответствующую книгу: ")
                            library.return_book(loan_id)     
                        elif user_choice == "3":
                            library.check_fines(user_id)
                        elif user_choice == "4":
                            title = input("Введите наименование книги: ")
                            author = input("Введите ФИО автора: ")
                            count = input("Введите количество книг: ")
                            if len(title) < 1 or not count.isdigit():
                                print("Ошибка создания книги!")
                                break
                            library.add_book(title, author, count)
                        elif user_choice == "5":
                            os.system('cls')
                            break
                        else:
                            print("Неправильный выбор. Попробуйте ещё раз.")
            elif choice == "2":
                username = input("Введите новый логин: ")
                password = input("Введите новый пароль: ")
                library.register_user(username, password)
            elif choice == "3":
                break
            else:
                print("Неправильный выбор. Попробуйте ещё раз.")
        except Exception as e:
            print("Возникла непридвиденная ошибка:", e)
if __name__ == "__main__":
    main()