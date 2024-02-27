import json
import sqlite3
import threading
from datetime import datetime, timedelta
from anvil.tables import app_tables
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import StringProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import SlideTransition
from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.pickers import MDDatePicker
from kivymd.uix.screen import MDScreen

from server import Server

# Create the BookSlot table if it doesn't exist

conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS BookSlot (
        slot_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        book_date TEXT NOT NULL,
        book_time TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
''')
conn.commit()


# Builder.load_file("slot_booking.kv")


class CButton(MDFlatButton):
    label_text = StringProperty("")
    slot_time = None

    def __init__(self, **kwargs):
        super(CButton, self).__init__(**kwargs)

        self.CButton_pressed = False
        self.default_md_bg_color = self.md_bg_color  # Store the default background color
        self.default_line_color = self.line_color  # Store the default line color

    def Slot_Timing(self, slot_timing):
        CButton.slot_time = slot_timing
        # Reset the colors of all buttons to their default state
        for button in self.parent.children:
            if isinstance(button, CButton):
                button.md_bg_color = button.default_md_bg_color
                button.line_color = button.default_line_color

        # Set the colors of the current button
        self.md_bg_color = (1, 0, 0, 0.1)  # Set background color
        self.line_color = (1, 0, 0, 0.5)  # Set line color
        self.CButton_pressed = True
        print(f"Selected time: {slot_timing}")

    pass


class Alert_Label(MDLabel):
    pass


class Slot_Booking(MDScreen):

    def __init__(self, **kwargs):
        super(Slot_Booking, self).__init__(**kwargs)
        Window.bind(on_keyboard=self.on_keyboard)
        threading.Thread(target=self.slot_days).start()
        self.book_slot_pressed = False
        self.server = Server()

    def on_keyboard(self, instance, key, scancode, codepoint, modifier):
        if key == 27:  # Keycode for the back button on Android
            self.on_back_button()
            return True
        return False

    # back button of slot_booking page
    def on_back_button(self, instance):
        self.manager.push_replacement("hospital_booking", "right")
        self.ids.CButton.clear_widgets()
        # reset all the buttons
        for button_id in ['button1', 'button2', 'button3', 'button4']:
            button = self.ids[button_id]
            button.elevation = 0
            button.md_bg_color = (1, 1, 1, 1)
            button.line_color = (1, 0, 0, 1)
        self.ids.available_slots_alert.text = "Choose a Day"
        print("Back To Hospital Page")

    # Book slot button logic
    date_list = []

    # upcoming 4 days Date is
    def slot_days(self):
        # Initialize empty lists to store dates and weekdays
        day_list = []
        # Get today's date
        today_date = datetime.now()
        # extracting Upcoming 4 days
        for i in range(0, 4):
            # Calculate the date for the next day in the loop
            next_date = today_date + timedelta(days=i)
            # Append the date to the date list
            self.date_list.append(next_date.strftime('%d-%m-%Y'))
            # Append the weekday to the day list
            day_list.append(next_date.strftime('%a'))
        # Now you have all dates in date_list and all weekdays in day_list
        dates = [date.split('-')[0] for date in self.date_list]
        print("Weekdays:", day_list)
        print("Dates:", self.date_list)
        day_button = ['day1', 'day2', 'day3', 'day4']
        date_button = ['date1', 'date2', 'date3', 'date4']
        # 4 buttons label gets updated
        for day_label, day, date_label, date in zip(day_button, day_list, date_button, dates):
            self.ids[day_label].text = day
            self.ids[date_label].text = date

    # logic for slot available for selected date
    time_list = ['09:00 AM', '11:00 AM', '01:00 PM', '03:00 PM', '05:00 PM', '07:00 PM']

    def Book_Slot(self, button_instance, day, date):

        self.book_slot_pressed = True
        self.selected_day = day  # Store the selected day

        for d in self.date_list:
            # Extract the day part from the date in Dates list
            day_part = d.split('-')[0]
            # Compare the day part with the given date
            if day_part == date:
                self.selected_date = d
                break  # Stop iterating if a match is found

        # Check if CButton widget exists before clearing it
        self.ids.CButton.clear_widgets()
        # reset all the buttons
        for button_id in ['button1', 'button2', 'button3', 'button4']:
            button = self.ids[button_id]
            button.elevation = 0
            button.md_bg_color = (1, 1, 1, 1)
            button.line_color = (1, 0, 0, 1)
        # Set  color for the clicked button
        button_instance.md_bg_color = (1, 0, 0, 0.1)
        button_instance.line_color = (1, 0, 0, 0.5)
        # If selected  date is equal to today's date
        if date == (datetime.now().strftime('%d')):

            # Get current time in 12-hour format with AM/PM
            current_time_str = datetime.now().strftime("%I:%M %p")
            print("Current time:", current_time_str)

            # Convert current time to a comparable format
            current_time_obj = datetime.strptime(current_time_str, "%I:%M %p")
            upper_limit = datetime.strptime('07:00 PM', "%I:%M %p")
            # Extract slot time for book_slot tabel
            selected_date = self.selected_date
            book_times_for_selected_date = self.get_book_times(selected_date)
            today_list = self.time_list.copy()  # Make a copy of time_list
            # Show slots which are available before '07:00 PM'
            updated_list = self.remove_duplicates(today_list, book_times_for_selected_date)
            # available slot above the current time
            available_slots = self.get_available_slots(updated_list, current_time_obj)
            # check current time is less the upper limit time
            if current_time_obj < upper_limit:
                # if updated_list is not empty
                if len(available_slots) > 0:
                    self.ids.available_slots_alert.text = "Available Slots"
                    for time_str in available_slots:
                        time_obj = datetime.strptime(time_str, "%I:%M %p")
                        if time_obj > current_time_obj:
                            # add button widget
                            custom = CButton(label_text=time_str)
                            self.ids.CButton.add_widget(custom)
                else :
                    # if all the slots are already booked
                    self.ids.available_slots_alert.text = f"Oops! No more slots available on {day}"

            else:
                # if current time is more than '07:00 PM'
                self.ids.available_slots_alert.text = f"Oops! No more slots available on {day}"
        else:
            # Extract slot time for book_slot tabel
            book_times_for_selected_date = self.get_book_times(self.selected_date)
            print(book_times_for_selected_date)
            next_day_list = self.time_list.copy()  # Make a copy of time_list
            # remove time_slots present in next_day_list:
            updated_list = self.remove_duplicates(next_day_list, book_times_for_selected_date)
            self.ids.available_slots_alert.text = "Available Slots"
            if len(updated_list) > 0:
                # Update the label

                # selected date is not equal to Current date then
                for time_str in updated_list:
                    custom = CButton(label_text=time_str)
                    self.ids.CButton.add_widget(custom)
            else:
                # if all the slots are already booked
                self.ids.available_slots_alert.text = f"Oops! No more slots available on {day}"

    # Extract slot time for book_slot tabel
    def get_book_times(self, selected_date):
        book_slot = app_tables.book_slot.search(book_date=selected_date)
        book_times = [row['book_time'] for row in book_slot]
        return book_times

    # remove the Time slot which are already booked for that day
    def remove_duplicates(self, next_day_list, book_times, capsules=2):
        updated_list = []
        for time_slot in next_day_list:
            if book_times.count(time_slot) < capsules:
                updated_list.append(time_slot)
        return updated_list

    def get_available_slots(self, updated_list, current_time_obj):
        available_slots = [time_slot for time_slot in updated_list if datetime.strptime(time_slot, "%I:%M %p") >= current_time_obj]
        return available_slots
    def pay_now(self, instance, *args):
        cbutton_pressed = any(
            button.CButton_pressed for button in self.ids.CButton.children if isinstance(button, CButton))
        if self.book_slot_pressed and cbutton_pressed:
            print("Date:", self.selected_date)
            print("Time:", CButton.slot_time)

            with open('user_data.json', 'r') as file:
                user_info = json.load(file)
            user_info['slot_date'] = self.selected_date
            user_info['slot_time'] = CButton.slot_time
            with open("user_data.json", "w") as json_file:
                json.dump(user_info, json_file)

            self.manager.push("payment_page")
        elif not self.book_slot_pressed and cbutton_pressed:
            self.show_validation_dialog("Select Date")
            print("Select Date")
        elif self.book_slot_pressed and not cbutton_pressed:
            self.show_validation_dialog("Select Time")
            print("Select Time")
        else:
            self.show_validation_dialog("Select Date and Time")
            print("Select Date and Time")

    def select_timings(self, button, label_text):
        self.session_time = label_text
        print(self.session_time)
        selected_slot = label_text
        for slot in Slot_Booking.time_slots:
            if slot == selected_slot:
                self.ids[slot].md_bg_color = (1, 1, 1, 1)
            else:
                self.ids[slot].md_bg_color = (1, 0, 0, 1)

    def slot_date_picker(self):
        current_date = datetime.now().date()
        date_dialog = MDDatePicker(year=current_date.year, month=current_date.month, day=current_date.day,
                                   size_hint=(None, None), size=(150, 150))
        date_dialog.bind(on_save=self.slot_save, on_cancel=self.slot_cancel)
        date_dialog.open()

    def slot_save(self, instance, value, date_range):
        # the date string in "year-month-day" format
        date_object = datetime.strptime(str(value), "%Y-%m-%d")
        # Format the date as "day-month-year"
        formatted_date = date_object.strftime("%d-%m-%Y")
        book_slot = app_tables.book_slot.search(book_date=formatted_date)
        book_times = [row['book_time'] for row in book_slot]
        print(formatted_date, book_times)
        for slots in Slot_Booking.time_slots:
            self.ids[slots].disabled = False
            if not book_times:
                print(book_times)
                for slots in Slot_Booking.time_slots:
                    self.ids[slots].disabled = False
            elif book_times:
                for slots in book_times:
                    self.ids[slots].disabled = True
            else:
                pass
        self.ids.date_choosed.text = formatted_date

    def show_validation_dialog(self, message):
        # Create the dialog asynchronously
        Clock.schedule_once(lambda dt: self._create_dialog(message), 0)

    def _create_dialog(self, message):
        dialog = MDDialog(
            text=f"{message}",
            elevation=0,
            buttons=[MDFlatButton(text="OK", on_release=lambda x: dialog.dismiss())],
        )
        dialog.open()
