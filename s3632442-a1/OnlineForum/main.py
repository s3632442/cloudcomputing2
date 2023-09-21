import datetime
import logging
import socket
import random  # Added for generating random user images
import os
from flask import Flask, request, render_template, redirect, url_for, session
from google.cloud import datastore
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Define the folder where uploaded images will be stored
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Configure Flask to use the UPLOAD_FOLDER
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Sample user data (replace with your user data)
user_data = {
    "User1": {"password": "password1", "image_url": "user1.jpg"},
    "User2": {"password": "password2", "image_url": "user2.jpg"},
    # Add more users as needed
}

def is_ipv6(addr):
    """Checks if a given address is an IPv6 address."""
    try:
        socket.inet_pton(socket.AF_INET6, addr)
        return True
    except OSError:
        return False

def store_message(datastore, username, subject, message_text, image_url):
    entity = datastore.Entity(key=datastore.key("message"))
    entity.update(
        {
            "user_message": message_text,
            "timestamp": datetime.datetime.now(tz=datetime.timezone.utc),
            "username": username,
            "subject": subject,
            "image_url": image_url,
        }
    )
    datastore.put(entity)

# Function to check if a file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to save an uploaded image and return its URL
def save_image(file):
    if file and allowed_file(file.filename):
        # Ensure the 'uploads' directory exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

        # Generate a unique filename (you may use a more robust approach)
        filename = secure_filename(file.filename)

        # Save the uploaded image to the 'uploads' folder
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Return the URL to the saved image
        return url_for('uploaded_file', filename=filename)

    # Return None if the file is not uploaded or has an invalid extension
    return None

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Check if the provided username exists in the user_data dictionary
        if username in user_data:
            stored_password = user_data[username]["password"]

            # Check if the provided password matches the stored password
            if password == stored_password:
                session["username"] = username
                return redirect(url_for("forum"))

        # If either the username or password is incorrect, redirect to the login page
        return redirect(url_for("login"))

    return """
    <html>
        <head><title>Login</title></head>
        <body>
            <h1>Login</h1>
            <form action="/" method="post">
                <div>
                    <label for="username">Username:</label>
                    <input type="text" name="username" id="username">
                </div>
                <div>
                    <label for="password">Password:</label>
                    <input type="password" name="password" id="password">
                </div>
                <div>
                    <input type="submit" value="Login">
                </div>
            </form>
        </body>
    </html>
    """

@app.route("/forum", methods=["GET", "POST"])
def forum():
    # Check if the user is logged in
    if "username" not in session:
        return redirect(url_for("login"))

    ds = datastore.Client()

    if request.method == "POST":
        subject = request.form["subject"]
        message_text = request.form["message"]

        # Handle image upload (you may need to adjust this based on your image storage method)
        if "image" in request.files:
            image_file = request.files["image"]
            # Save the image to a storage location and get its URL
            image_url = save_image(image_file)  # Implement the 'save_image' function

        # Store the submitted data in the datastore (or your chosen storage)
        store_message(ds, session["username"], subject, message_text, image_url)

    query = ds.query(kind="message", order=("-timestamp",))

    messages = []
    for message_entity in query.fetch(limit=10):
        user_message = message_entity.get("user_message", "Message content not found.")
        username = message_entity.get("username", "Unknown User")
        subject = message_entity.get("subject", "No Subject")
        image_url = message_entity.get("image_url", None)
        messages.append({"username": username, "subject": subject, "message": user_message, "image_url": image_url})

    return render_template("forum.html", username=session["username"], messages=messages)


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
