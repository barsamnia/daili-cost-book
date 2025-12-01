# combined_app.py
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.graphics import Color, RoundedRectangle
from kivy.clock import Clock
from kivy.core.window import Window

import os
import pandas as pd
from datetime import datetime
import uuid

# ---- Config default ----
Window.softinput_mode = "pan"
DEFAULT_DOWNLOAD_DIR = "/storage/emulated/0/Download"
DEFAULT_FILE_NAME = "purchace_pro_ver.xlsx"

def file_path_from_dir(directory, filename=DEFAULT_FILE_NAME):
    return os.path.join(directory, filename)

# ---- Excel system ----
def ensure_excel_file(path):
    directory = os.path.dirname(path)
    if not os.path.exists(directory):
        os.makedirs(directory)

    if not os.path.exists(path):
        df = pd.DataFrame({
            "ID": pd.Series(dtype="str"),
            "Title": pd.Series(dtype="str"),
            "Amount": pd.Series(dtype="float"),
            "Type": pd.Series(dtype="str"),
            "Category": pd.Series(dtype="str"),
            "Timestamp": pd.Series(dtype="str")
        })
        df.to_excel(path, index=False)
    return pd.read_excel(path)

def calculate_balance(df):
    income = df[df["Type"]=="income"]["Amount"].sum()
    expense = df[df["Type"]=="expense"]["Amount"].sum()
    return income - expense

def add_purchase(title, amount, ttype, category, path):
    df = ensure_excel_file(path)
    df_no_balance = df[df["Title"] != "__BALANCE__"]
    new_row = pd.DataFrame([{
        "ID": str(uuid.uuid4()),
        "Title": title,
        "Amount": amount,
        "Type": ttype,
        "Category": category,
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }])
    df_concat = pd.concat([df_no_balance, new_row], ignore_index=True)
    balance = calculate_balance(df_concat)
    balance_row = pd.DataFrame([{
        "ID": "",
        "Title": "__BALANCE__",
        "Amount": balance,
        "Type": "summary",
        "Category": "",
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }])
    df_final = pd.concat([df_concat, balance_row], ignore_index=True)
    df_final.to_excel(path, index=False)

# ---- UI App ----
class CombinedApp(App):
    def build(self):
        # Current file path
        self.download_dir = DEFAULT_DOWNLOAD_DIR
        self.file_name = DEFAULT_FILE_NAME
        self.file_path = file_path_from_dir(self.download_dir, self.file_name)

        # Root container
        root = BoxLayout(orientation='vertical')
        with root.canvas.before:
            Color(0.08,0.08,0.08,1)
            self.bg = RoundedRectangle(size=root.size, pos=root.pos)
        root.bind(size=self.update_bg, pos=self.update_bg)

        # ScrollView
        scroll = ScrollView(size_hint=(1,1))

        # Main Box
        self.main_box = BoxLayout(orientation='vertical', spacing=20, padding=16, size_hint_y=None)
        self.main_box.bind(minimum_height=self.main_box.setter('height'))

        # ---- Select Folder ----
        self.btn_select_folder = Button(
            text=f"Select Folder\n({self._short_dir(self.download_dir)})",
            size_hint=(1,None),
            height=80,
            font_size=26,
            background_normal="",
            background_color=(0.18,0.18,0.18,1),
            color=(1,1,1,1)
        )
        self.btn_select_folder.bind(on_press=self.open_folder_chooser)
        self.main_box.add_widget(self.btn_select_folder)

        # ---- Categories ----
        self.category_box = BoxLayout(orientation='vertical', spacing=14, padding=14,
                                      size_hint=(1,None))
        self.category_box.bind(minimum_height=self.category_box.setter('height'))

        with self.category_box.canvas.before:
            Color(0.12,0.12,0.12,1)
            self.cat_bg = RoundedRectangle(size=self.category_box.size, pos=self.category_box.pos, radius=[28])
        self.category_box.bind(size=self.update_cat_bg, pos=self.update_cat_bg)

        self.category_box.add_widget(Label(text="Select Category:", font_size=28, color=(1,1,1,1),
                                           size_hint_y=None, height=40))

        # Checkboxes
        self.ch1 = CheckBox(size_hint=(None,None), size=(50,50))
        self.ch2 = CheckBox(size_hint=(None,None), size=(50,50))
        self.ch3 = CheckBox(size_hint=(None,None), size=(50,50))

        for ch in [self.ch1, self.ch2, self.ch3]:
            ch.bind(active=self.on_checkbox_select)

        def make_row(ch, txt):
            row = BoxLayout(orientation='horizontal', height=50, size_hint_y=None)
            row.add_widget(ch)
            row.add_widget(Label(text=txt, markup=True, font_size=26, color=(1,1,1,1)))
            return row

        self.category_box.add_widget(make_row(self.ch1, "[b]Income[/b]"))
        self.category_box.add_widget(make_row(self.ch2, "[b]Essential Expense[/b]"))
        self.category_box.add_widget(make_row(self.ch3, "[b]Non-Essential Expense[/b]"))

        self.main_box.add_widget(self.category_box)

        # ---- Input Fields ----
        self.lbl1 = Label(text="Title", font_size=28, color=(1,1,1,1), size_hint_y=None, height=50)
        self.txt1 = TextInput(font_size=26, height=70, size_hint_y=None)

        self.lbl2 = Label(text="Amount", font_size=28, color=(1,1,1,1), size_hint_y=None, height=50)
        self.txt2 = TextInput(font_size=26, height=70, size_hint_y=None, input_filter="float")

        self.main_box.add_widget(self.lbl1)
        self.main_box.add_widget(self.txt1)
        self.main_box.add_widget(self.lbl2)
        self.main_box.add_widget(self.txt2)

        # ---- Save Button ----
        self.btn_send = Button(
            text="Save Entry",
            size_hint=(1,None),
            height=90,
            font_size=28,
            background_normal="",
            background_color=(0.22,0.22,0.22,1),
            color=(1,1,1,1)
        )
        self.btn_send.bind(on_press=self.save_entry)
        self.main_box.add_widget(self.btn_send)

        scroll.add_widget(self.main_box)
        root.add_widget(scroll)

        return root

    # ----- UI helpers -----
    def update_bg(self, instance, value):
        self.bg.size = instance.size
        self.bg.pos = instance.pos

    def update_cat_bg(self, instance, value):
        self.cat_bg.size = instance.size
        self.cat_bg.pos = instance.pos

    def _short_dir(self, d, length=32):
        return d if len(d) <= length else "..." + d[-(length-3):]

    def on_checkbox_select(self, checkbox, value):
        if value:
            for ch in [self.ch1, self.ch2, self.ch3]:
                if ch is not checkbox:
                    ch.active = False

    # ----- Save Logic -----
    def save_entry(self, instance):
        title = self.txt1.text.strip()
        amount = self.txt2.text.strip()

        if not (self.ch1.active or self.ch2.active or self.ch3.active):
            return self.dark_popup("⚠ Please select a category")

        if not title or not amount:
            return self.dark_popup("❌ Please fill both fields")

        try:
            amount = float(amount)
        except:
            return self.dark_popup("❌ Invalid amount")

        if self.ch1.active:
            ttype, category = "income", "income"
        elif self.ch2.active:
            ttype, category = "expense", "essential"
        else:
            ttype, category = "expense", "non-essential"

        try:
            add_purchase(title, amount, ttype, category, self.file_path)
        except Exception as e:
            return self.dark_popup(f"❌ Failed to save:\n{e}")

        msg = (
            "✔ Entry saved successfully\n\n"
            f"[b]Title:[/b] {title}\n"
            f"[b]Amount:[/b] {amount}\n"
            f"[b]Type:[/b] {ttype}\n"
            f"[b]Category:[/b] {category}\n\n"
            f"[b]Saved at:[/b]\n{self.file_path}"
        )

        self.dark_popup(msg)

        self.txt1.text = ""
        self.txt2.text = ""
        for ch in [self.ch1, self.ch2, self.ch3]:
            ch.active = False

    # ----- Dark Popup -----
    def dark_popup(self, msg):
        content = BoxLayout(orientation="vertical", padding=20, spacing=16)
        with content.canvas.before:
            Color(0.08, 0.08, 0.08, 1)
            bg = RoundedRectangle(size=content.size, pos=content.pos, radius=[20])
        content.bind(size=lambda i,v: setattr(bg,'size',v))
        content.bind(pos=lambda i,v: setattr(bg,'pos',v))

        lbl = Label(
            text=msg,
            markup=True,
            font_size=24,
            color=(1,1,1,1),
            halign="left",
            valign="middle"
        )
        lbl.bind(size=lambda s, v: setattr(lbl, "text_size", v))

        btn = Button(
            text="OK",
            size_hint_y=None,
            height=70,
            background_normal="",
            background_color=(0.2,0.2,0.2,1),
            color=(1,1,1,1),
            font_size=24
        )

        popup = Popup(title="", content=content, size_hint=(0.92,0.55), auto_dismiss=False)
        btn.bind(on_release=popup.dismiss)

        content.add_widget(lbl)
        content.add_widget(btn)
        popup.open()

    # ----- Folder Chooser -----
    def open_folder_chooser(self, instance):
        chooser = FileChooserListView(path=self.download_dir, dirselect=True)
        box = BoxLayout(orientation='vertical', spacing=8, padding=8)
        box.add_widget(chooser)

        btns = BoxLayout(size_hint_y=None, height=60, spacing=8)
        btn_cancel = Button(text="Cancel")
        btn_select = Button(text="Choose")
        btns.add_widget(btn_cancel)
        btns.add_widget(btn_select)
        box.add_widget(btns)

        popup = Popup(title="Select Folder", content=box, size_hint=(0.95,0.85), auto_dismiss=False)
        btn_cancel.bind(on_release=popup.dismiss)

        def choose(*args):
            if chooser.selection:
                chosen = chooser.selection[0]
                if os.path.isdir(chosen):
                    self.download_dir = chosen
                    self.file_path = file_path_from_dir(chosen, self.file_name)
                    self.btn_select_folder.text = f"Select Folder\n({self._short_dir(self.download_dir)})"
                    popup.dismiss()
                    self.dark_popup(f"Folder set:\n{self.download_dir}")
                    return
            self.dark_popup("Invalid folder!")

        btn_select.bind(on_release=choose)
        popup.open()

# ---- Run App ----
if __name__ == "__main__":
    CombinedApp().run()