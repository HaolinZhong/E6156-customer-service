
from flask import Flask, request, jsonify
from dbservice import CustomerRepository
import os
from flask_cors import CORS

application = Flask(__name__)
CORS(application)

application.secret_key = os.environ.get("SESSION_KEY")

session = {}

@application.route('/customer/get/<string:email>', methods=['GET'])
def get_customer_info(email):
    res = CustomerRepository.get_customer_by_email(email)
    if res:
        rsp = jsonify(res)
    else:
        rsp = {"message": "user not found"}

    return rsp

@application.route('/customer/login', methods=['POST'])
def customer_login():
    content = request.json
    email, password = content['email'], content['password']
    res = CustomerRepository.validate_login(email, password)

    if res:
        user = CustomerRepository.get_customer_by_email(email)
        session[email] = user
        return user
    else:
        return {"message": "invalid email/password"}


@application.route('/customer/glogin', methods=['POST'])
def google_login():
    # Find out what URL to hit for Google login
    content = request.json
    email, fname, lname = content['email'], content['fname'], content['lname']

    if not CustomerRepository.get_customer_by_email(email):
        CustomerRepository.register_user(email, fname, lname, 'login_by_google', None)

    user = CustomerRepository.get_customer_by_email(email)
    # Begin user session by logging the user in
    session[email] = user

    return user

@application.route('/customer/validate_login/<string:email>')
def validate_login(email):
    return jsonify({"has_login": email in session})

@application.route('/customer/logout/<string:email>')
def customer_logout(email):
    if email in session:
        session.pop(email)
        return {"message":"logout success!"}
    return {"message":"user has not login!"}

@application.route('/customer/register', methods=['POST'])
def customer_register():
    f = request.form
    email, fname, lname, phone, password = f['email'], f['fname'], f['lname'], f['phone'], f['password']
    res = CustomerRepository.register_user(email, fname, lname, phone, password)

    if not res: return {"message": "register failed! email may be registered."}

    return {"message": "register success!"}


@application.route('/customer/update/', methods=['PATCH'])
def update_profile():
    if 'user' not in session:
        return {"message": "user has not login!"}
    f, new = request.form, {}
    new['first_name'], new['last_name'], new['phone_number'] = f['fname'], f['lname'], f['phone']
    row_affected = CustomerRepository.update_user_profile(session['user']['email'], new)

    if row_affected == 0: return {'message': 'update failed!'}
    session['user'] = CustomerRepository.get_customer_by_email(session['user']['email'])
    return {'message': 'update success!'}


if __name__ == "__main__":
    application.run(ssl_context="adhoc")
