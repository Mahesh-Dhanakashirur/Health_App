from kivymd.uix.screen import MDScreen

from form_validation import BaseRegistrationScreen


class OxyGymServiceDoc(BaseRegistrationScreen):

    def file_manager_open(self, field_id):
        super().file_manager_open(field_id)