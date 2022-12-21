import json

from flask import Flask, request, Response, jsonify, session, redirect, url_for
from dbservice import CustomerRepository
import os
from oauthlib.oauth2 import WebApplicationClient
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

app.secret_key = os.environ.get("SESSION_KEY")

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

client = WebApplicationClient(GOOGLE_CLIENT_ID)

@app.route('/')
def index():
    if 'user' in session:
        return {'user': session["user"]}
    return '<a class="button" href="/v1/customer/glogin">Google Login</a>'

def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


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
@app.route('/v1/customer/glogin', methods=['GET'])
def google_login():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    print(request.base_url + "/callback")
    return redirect(request_uri)

@app.route("/v1/customer/glogin/callback", methods=['GET'])
def google_login_callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send a request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Now that you have tokens (yay) let's find and hit the URL
    # from Google that gives you the user's profile information,
    # including their Google profile image and email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    # Doesn't exist? Add it to the database.
    if not CustomerRepository.get_customer_by_email(users_email):
        CustomerRepository.register_user(users_email, users_name, '', 'login_by_google', None)

    # Begin user session by logging the user in
    session['user'] = CustomerRepository.get_customer_by_email(users_email)

    # Send user back to homepage
    return redirect(url_for("index"))

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


if __name__ == "__main__":
    app.run(ssl_context="adhoc")
