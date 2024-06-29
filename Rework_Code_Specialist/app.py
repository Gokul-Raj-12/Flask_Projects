from flask import Flask, abort, session, redirect, request
import requests 
from cachecontrol import CacheControl
import google.auth.transport.requests
from google_auth_oauthlib.flow import Flow
import os
from google.oauth2 import id_token
import pathlib

app = Flask("Google Login App")
app.secret_key = "trip.py"

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

GOOGLE_CLIENT_ID = "62946963234-8kvuc5fso2e93gdh4f55ibmh8k0cumu2.apps.googleusercontent.com"
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="http://127.0.0.1:5000/callback" )

def login_is_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return abort(401) #Authorization required
        else:
            return function(*args, **kwargs)
    return wrapper 

@app.route("/login")
def login():
    authorization_url, state = flow.authorization_url() 
    session["state"] = state 
    return redirect(authorization_url)

@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)
    
    if not session["state"] == request.args.get("state"):
        abort(500) #State does not match!
        
    credentials = flow.credentials 
    request_session = requests.session()
    cached_session = CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)
    
    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )
    return id_info

@app.route("/logout")
def logout():
    session.clear()
    return redirect ("/")

@app.route("/")
def index():
    return ("hello world       <a href='/login'><button>Login</button></a>")

@app.route("/protected_area")
@login_is_required
def protected_area():
    return ("protected_area"      "<a href='/logout'><button>Logout</button></a>")

if __name__ == "__main__":
    app.run(debug=True)
    