from flask import Flask, request, Response, jsonify, session, redirect, url_for
from dbservice import CustomerRepository
import os

app = Flask(__name__)

app.secret_key = os.environ.get("SESSION_KEY")

@app.route('/')
def index():
    if 'user' in session:
        return {'user': session["user"]}
    return {'message': 'user has not login!'}

@app.route('/v1/customer/get/<string:email>', methods=['GET'])
def get_customer_info(email):
    res = CustomerRepository.get_customer_by_email(email)
    if res:
        rsp = jsonify(res)
    else:
        rsp = {"message": "user not found"}

    return rsp


@app.route('/v1/customer/login', methods=['POST'])
def customer_login():
    email, password = request.form['email'], request.form['password']
    res = CustomerRepository.validate_login(email, password)

    if res:
        session['user'] = CustomerRepository.get_customer_by_email(email)
        return {"message": "login success!"}
    else:
        return {"message": "invalid email/password"}

@app.route('/v1/customer/logout')
def customer_logout():
    if 'user' in session:
        session.pop('user')
        return {"message":"logout success!"}
    return {"message":"user has not login!"}

@app.route('/v1/customer/register', methods=['POST'])
def customer_register():
    f = request.form
    email, fname, lname, phone, password = f['email'], f['fname'], f['lname'], f['phone'], f['password']
    res = CustomerRepository.register_user(email, fname, lname, phone, password)

    if not res: return {"message": "register failed! email may be registered."}

    return {"message": "register success!"}


@app.route('/v1/customer/update/', methods=['PATCH'])
def update_profile():
    if 'user' not in session:
        return {"message": "user has not login!"}
    f, new = request.form, {}
    new['first_name'], new['last_name'], new['phone_number'] = f['fname'], f['lname'], f['phone']
    row_affected = CustomerRepository.update_user_profile(session['user']['email'], new)

    if row_affected == 0: return {'message': 'update failed!'}
    session['user'] = CustomerRepository.get_customer_by_email(session['user']['email'])
    return {'message': 'update success!'}


if __name__ == '__main__':
    app.run()
