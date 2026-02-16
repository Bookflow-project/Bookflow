import sqlite3
import hashlib

class DBManager:
    _instance = None

    def __new__(cls, db_name="library.db"):
        if cls._instance is None:
            cls._instance = super(DBManager, cls).__new__(cls)
            cls._instance.db_name = db_name
            cls._instance._create_tables()
        return cls._instance

    def connect(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_tables(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                email VARCHAR(255),
                login VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
                book_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(255),
                author VARCHAR(255),
                file_path VARCHAR(255),
                current_page INTEGER DEFAULT 0, 
                user_id INTEGER,
                FOREIGN KEY(user_id) REFERENCES users(user_id),
                UNIQUE(user_id, file_path)
            )
        ''')
        conn.commit()
        conn.close()

    def register_user(self, email, login, password):
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (email, login, password_hash) VALUES (?, ?, ?)", 
                           (email, login, pwd_hash))
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return True, user_id
        except sqlite3.IntegrityError:
            conn.close()
            return False, "Логин занят"

    def login_user(self, login, password):
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE login = ? AND password_hash = ?", (login, pwd_hash))
        user = cursor.fetchone()
        conn.close()
        return (True, user['user_id']) if user else (False, None)

    def add_book(self, user_id, title, author, path):
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO books (title, author, file_path, user_id, current_page) VALUES (?, ?, ?, ?, 0)",
                        (title, author, path, user_id))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False

    def get_user_books(self, user_id):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM books WHERE user_id = ?", (user_id,))
        books = cursor.fetchall()
        conn.close()
        return books

    def delete_book(self, book_id):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM books WHERE book_id = ?", (book_id,))
        conn.commit()
        conn.close()

    def update_book_progress(self, book_id, page_num):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("UPDATE books SET current_page = ? WHERE book_id = ?", (page_num, book_id))
        conn.commit()
        conn.close()

    def get_book_progress(self, book_id):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT current_page FROM books WHERE book_id = ?", (book_id,))
        result = cursor.fetchone()
        conn.close()
        return result['current_page'] if result else 0