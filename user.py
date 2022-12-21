from flask_login import UserMixin

from dbservice import CustomerRepository

class User(UserMixin):
    def __init__(self, id_, fname, lname, email, phone):
        self.id = id_
        self.fname = fname
        self.lname = lname
        self.email = email
        self.phone = phone

    @staticmethod
    def get(user_id):
        user = CustomerRepository.get_customer_by_email(user_id)
        if not user:
            return None
        return user

    @staticmethod
    def create(email, fname, lname, phone, password):
        CustomerRepository.register_user(email, fname, lname, phone, password)