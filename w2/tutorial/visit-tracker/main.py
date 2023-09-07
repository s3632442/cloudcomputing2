import datetime
from flask import Flask, render_template, request
from google.auth.transport import requests
from google.cloud import datastore
import google.oauth2.id_token

firebase_request_adapter = requests.Request()
datastore_client = datastore.Client()

app = Flask(__name__)

def store_time(email, dt):
    entity = datastore.Entity(key=datastore_client.key("User", email, "visit"))
    entity.update({"timestamp": dt})
    datastore_client.put(entity)

def fetch_times(email, limit):
    ancestor = datastore_client.key("User", email)
    query = datastore_client.query(kind="visit", ancestor=ancestor)
    query.order = ["-timestamp"]
    times = query.fetch(limit=limit)
    return times

@app.route("/")
def root():
    # Verify Firebase auth.
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    times = None

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            store_time(claims["email"], datetime.datetime.now(tz=datetime.timezone.utc))
            times = fetch_times(claims["email"], 10)
        except ValueError as exc:
            error_message = str(exc)

    return render_template("index.html", user_data=claims, error_message=error_message, times=times)

if __name__ == "__main__":
    app.run()
