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

db = DBManager()

class LoginScreen(Screen):
    def do_login(self):
        login = self.login_input.text
        password = self.pass_input.text
        success, result = db.login_user(login, password)
        if success:
            App.get_running_app().current_user_id = result
            self.manager.get_screen('library').load_books(force=True)
            self.manager.current = 'library'
        #TO DO reset
        else:
            self.error_label.text = "Ошибка входа"

class BookFlowApp(App):
    current_user_id = None
    def build(self):
        return Builder.load_file('interface.kv')

if __name__ == '__main__':
    BookFlowApp().run()
