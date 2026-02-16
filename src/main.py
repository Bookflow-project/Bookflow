import os
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import StringProperty, ObjectProperty
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.clock import Clock
from kivy.animation import Animation

from database import DBManager
from core import BookParserFactory, BaseMuPDFBook

db = DBManager()

class ClickableImage(ButtonBehavior, Image):
    pass

class WelcomeScreen(Screen):
    pass

class LoginScreen(Screen):
    def do_login(self):
        login = self.login_input.text
        password = self.pass_input.text
        success, result = db.login_user(login, password)
        if success:
            App.get_running_app().current_user_id = result
            self.manager.get_screen('library').load_books(force=True)
            self.manager.current = 'library'
            self.reset()
        else:
            self.error_label.text = "Ошибка входа"
    def reset(self):
        self.login_input.text = ""
        self.pass_input.text = ""
        self.error_label.text = ""

class RegisterScreen(Screen):
    def do_register(self):
        email = self.email_input.text
        login = self.login_input.text
        password = self.pass_input.text
        if not login or not password:
            self.error_label.text = "Заполните поля"
            return
        success, result = db.register_user(email, login, password)
        if success:
            _, uid = db.login_user(login, password)
            App.get_running_app().current_user_id = uid
            self.manager.get_screen('library').load_books(force=True)
            self.manager.current = 'library'
            self.reset()
        else:
            self.error_label.text = result
    def reset(self):
        self.email_input.text = ""
        self.login_input.text = ""
        self.pass_input.text = ""

class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)
    path = StringProperty(os.path.expanduser("~"))

class BookItem(BoxLayout):
    title = StringProperty()
    author = StringProperty()
    cover_texture = ObjectProperty(None)
    cover_source = StringProperty("")

    def __init__(self, book_id, file_path, **kwargs):
        super().__init__(**kwargs)
        self.book_id = book_id
        self.file_path = file_path
        self.load_cover()

    def load_cover(self):
        try:
            parser = BookParserFactory.get_parser(self.file_path)
            if isinstance(parser, BaseMuPDFBook):
                texture = parser.get_cover_texture(self.file_path)
                if texture:
                    self.cover_texture = texture
        except Exception as e:
            print(f"Cover load error: {e}")

    def open_book(self):
        app = App.get_running_app()
        app.root.get_screen('reader').load_book(self.book_id, self.file_path)
        app.root.current = 'reader'

    def delete_book(self):
        db.delete_book(self.book_id)
        App.get_running_app().root.get_screen('library').load_books(force=True)

class LibraryScreen(Screen):
    _loading = False
    all_books_cache = []

    def load_books(self, force: bool = False, filter_text: str = ""):
        if self._loading: return
        self._loading = True
        try:
            self.book_list.clear_widgets()
            user_id = App.get_running_app().current_user_id
            if user_id is None: return

            if force or not self.all_books_cache:
                self.all_books_cache = db.get_user_books(user_id)

            books_to_show = []
            if filter_text:
                ft = filter_text.lower()
                for book in self.all_books_cache:
                    if ft in book['title'].lower():
                        books_to_show.append(book)
            else:
                books_to_show = self.all_books_cache

            seen = set()
            for book in books_to_show:
                bid = book['book_id']
                if bid in seen: continue
                seen.add(bid)
                item = BookItem(
                    book_id=bid,
                    file_path=book['file_path'],
                    title=book['title'],
                    author=book['author']
                )
                self.book_list.add_widget(item)
        finally:
            self._loading = False

    def filter_books(self, text):
        self.load_books(force=False, filter_text=text)

    def show_add_dialog(self):
        content = LoadDialog(load=self.load_file, cancel=self.dismiss_popup)
        self._popup = Popup(title="Выберите книгу", content=content,
                            size_hint=(0.9, 0.9),
                            title_color=(1, 1, 1, 1),
                            title_align='center',
                            separator_height=0,
                            padding=0,
                            background='', 
                            background_color=(0.2, 0.2, 0.2, 1))
        self._popup.open()

    def load_file(self, path, filename):
        if filename:
            selected_path = filename[0]
            self.dismiss_popup()
            Clock.schedule_once(lambda dt: self._add_book_logic(selected_path), 0.1)

    def dismiss_popup(self):
        self._popup.dismiss()

    def _add_book_logic(self, path):
        try:
            user_id = App.get_running_app().current_user_id
            parser = BookParserFactory.get_parser(path)
            meta = parser.parse_metadata(path)
            if db.add_book(user_id, meta['title'], meta['author'], path):
                self.load_books(force=True)
            else:
                print("Книга уже есть в базе")
        except Exception as e:
            print(f"Error adding book: {e}")

class ReaderScreen(Screen):
    current_page = 0
    total_pages = 0
    doc = None
    parser = None
    controls_visible = True
    current_book_id = None

    def load_book(self, book_id, file_path):
        self.doc = None
        self.current_book_id = book_id
        self.controls_visible = True
        self.ids.top_bar.opacity = 1
        self.ids.bottom_bar.opacity = 1
        
        self.reset_zoom()

        try:
            try: self.book_image.texture = None
            except: pass

            self.parser = BookParserFactory.get_parser(file_path)
            if isinstance(self.parser, BaseMuPDFBook):
                self.doc = self.parser.open_document(file_path)
                self.total_pages = self.doc.page_count
                
                saved_page = db.get_book_progress(book_id)
                if saved_page >= self.total_pages:
                    saved_page = 0
                
                self.current_page = saved_page
                self.show_page(self.current_page)
            else:
                self.page_label.text = "Формат не поддерживается"
        except Exception as e:
            self.page_label.text = f"Ошибка: {str(e)}"

    def reset_zoom(self):
        """Сбрасывает масштаб и позицию Scatter"""
        if self.book_scatter:
            self.book_scatter.scale = 1
            self.book_scatter.pos = (0, 0)

    def show_page(self, page_num):
        if not self.doc: return
        texture = self.parser.get_page_texture(self.doc, page_num)
        if texture:
            self.book_image.texture = texture
            self.page_label.text = f"{page_num + 1} / {self.total_pages}"

    def next_page(self):
        if self.doc and self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.reset_zoom()
            self.show_page(self.current_page)
            self.save_progress()

    def prev_page(self):
        if self.doc and self.current_page > 0:
            self.current_page -= 1
            self.reset_zoom()
            self.show_page(self.current_page)
            self.save_progress()

    def save_progress(self):
        if self.current_book_id is not None:
            db.update_book_progress(self.current_book_id, self.current_page)

    def close_book(self):
        self.save_progress()
        if self.doc:
            self.doc.close()
        App.get_running_app().root.current = 'library'

    def toggle_controls(self):
        self.controls_visible = not self.controls_visible
        target_opacity = 1 if self.controls_visible else 0
        anim = Animation(opacity=target_opacity, duration=0.2)
        anim.start(self.ids.top_bar)
        anim.start(self.ids.bottom_bar)

class BookFlowApp(App):
    current_user_id = None 
    def build(self):
        return Builder.load_file('interface.kv')

if __name__ == '__main__':
    BookFlowApp().run()