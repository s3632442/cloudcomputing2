import datetime
import logging
import socket
import random  # Added for generating random user images

from flask import Flask, request, session, redirect, url_for, render_template
from google.cloud import datastore

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Sample user data (replace with your user data)
user_data = {
    "s3456": {"username": "User1", "image_url": "user1.jpg"},
    "s3210": {"username": "User2", "image_url": "user2.jpg"},
    # Add more users as needed
}

def is_ipv6(addr):
    """Checks if a given address is an IPv6 address."""
    try:
        socket.inet_pton(socket.AF_INET6, addr)
        return True
    except OSError:
        return False

@app.route("/", methods=["GET", "POST"])
def index():
    if "username" not in session:
        return redirect(url_for("login"))

    ds = datastore.Client()

    if request.method == "POST" and "message" in request.form:
        user_message = request.form["message"]
        entity = datastore.Entity(key=ds.key("message"))
        entity.update(
            {
                "user_message": user_message,
                "timestamp": datetime.datetime.now(tz=datetime.timezone.utc),
                "username": session["username"]
            }
        )
        ds.put(entity)

    query = ds.query(kind="message", order=("-timestamp",))

    messages = []
    for message_entity in query.fetch(limit=10):
        user_message = message_entity.get("user_message", "Message content not found.")
        username = message_entity.get("username", "Unknown User")
        messages.append({"username": username, "message": user_message})

    return render_template("index.html", username=session["username"], messages=messages)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["username"] = request.form["username"]
        return redirect(url_for("index"))

    return """
    <html>
        <head><title>Login</title></head>
        <body>
            <h1>Login</h1>
            <form action="/login" method="post">
                <div>
                    <label for="username">Username:</label>
                    <input type="text" name="username" id="username">
                </div>
                <div>
                    <input type="submit" value="Login">
                </div>
            </form>
        </body>
    </html>
    """

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

@app.route("/user/<username>")
def user(username):
    if username not in user_data:
        return "User not found", 404

    user_info = user_data[username]
    return render_template("user.html", username=username, user_info=user_info)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
