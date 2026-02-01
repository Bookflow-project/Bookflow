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


class BookFlowApp(App):
    current_user_id = None
    def build(self):
        return Builder.load_file('interface.kv')

if __name__ == '__main__':
    BookFlowApp().run()
