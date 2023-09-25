import random
import datetime
import socket
import random  # Added for generating random user images
import os
from flask import Flask, request, render_template, redirect, url_for, session
from google.cloud import datastore
from werkzeug.utils import secure_filename
from google.cloud import storage


app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

datastore_client = datastore.Client()
storage_client = storage.Client()
bucket_name = 'exampleapp-398810.appspot.com'  # Replace with your bucket name


# Define the folder where uploaded images will be stored
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Configure Flask to use the UPLOAD_FOLDER
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Sample user data (replace with your user data)
# user_data = {
#     "User1": {"password": "password1", "image_url": "user1.jpg"},
#     "User2": {"password": "password2", "image_url": "user2.jpg"},
#     # Add more users as needed
# }

def count_users():
    query = datastore_client.query(kind="user_data")
    return len(list(query.fetch()))


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

        # Check if the provided username exists in the user_data entity kind
        query = datastore_client.query(kind="user_data")
        query.add_filter("username", "=", username)
        user_entities = query.fetch(limit=1)  # Use limit to fetch a single result

        user_entity = next(user_entities, None)  # Get the first result or None if not found

        if not user_entity:
            # Username does not exist
            return redirect(url_for("login"))

        stored_password = user_entity.get("password")

        # Check if the provided password matches the stored password
        if password == stored_password:
            session["username"] = username
            return redirect(url_for("forum"))

        # If the password is incorrect, redirect to the login page
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
            <p>Don't have an account? <a href="/register">Register here</a></p>
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
    
    # Create a dictionary to store user images
    user_images = {}

    for message_entity in query.fetch(limit=10):
        user_message = message_entity.get("user_message", "Message content not found.")
        username = message_entity.get("username", "Unknown User")
        subject = message_entity.get("subject", "No Subject")
        image_url = message_entity.get("image_url", None)

        # Store the image URL for this user
        if username and image_url:
            user_images[username] = image_url

        messages.append({"username": username, "subject": subject, "message": user_message, "image_url": image_url})

    # Debugging: Print user_images and message.username values
    print("user_images:", user_images)
    for message in messages:
        print("message.username:", message["username"])

    return render_template("forum.html", username=session["username"], messages=messages, user_images=user_images)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        id = request.form["id"]
        username = request.form["username"]
        password = request.form["password"]
        
        # Get the uploaded image file from the request
        image_file = request.files["image"]

        # Validate the ID and username against Datastore
        if validate_id_and_username(id, username):
            # If ID and username are valid, store registration information
            store_registration_data(id, username, password, image_file)
            return render_template("registration_successful.html")  # Render the success page
        else:
            return render_template("invalid_id_username.html")  # Render the invalid ID or username page

    return render_template("registration.html")


from google.cloud import datastore

def validate_id_and_username(id, username):
    # Check if the provided `id` and `username` are not empty
    if not id or not username:
        return False

    # Initialize the Datastore client
    datastore_client = datastore.Client()

    # Query the Datastore to check if the ID and username already exist
    query = datastore_client.query(kind="user_data")
    query.add_filter("id", "=", id)
    query.add_filter("username", "=", username)

    # Execute the query and check if any results are returned
    result = list(query.fetch())

    # If there are no results, the ID and username are unique and valid
    return not bool(result)


def store_registration_data(id, username, password, image_file):
    # Initialize the Datastore client
    datastore_client = datastore.Client()

    # Initialize the Storage client and specify your bucket name
    storage_client = storage.Client()
    bucket_name = 'exampleapp-398810.appspot.com'  # Replace with your bucket name

    # Create a unique filename for the user image
    filename = secure_filename(image_file.filename)

    # Specify the object name (this is how the file will be stored in the bucket)
    object_name = f"images/{filename}"  # You can adjust the object name structure as needed

    # Save the user image to your storage with the specified object name
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(object_name)
    blob.upload_from_string(image_file.read(), content_type=image_file.content_type)

    # Get the URL of the uploaded image
    image_url = blob.public_url

    # Create a Datastore entity for the user registration
    entity = datastore.Entity(key=datastore_client.key("user_data"))
    entity.update({
        "id": id,
        "username": username,
        "password": password,  # Remember to securely hash the password
        "image_url": image_url,
    })

    # Store the registration information in Datastore
    datastore_client.put(entity)


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

@app.route("/user/<username>")
def user(username):
    # Query the Datastore for user data based on the provided username
    query = datastore_client.query(kind="user_data")
    query.add_filter("username", "=", username)
    user_entities = list(query.fetch(limit=1))  # Convert to a list to check if it's empty

    if not user_entities:
        return "User not found", 404

    user_entity = user_entities[0]  # Get the first result
    user_info = {
        "username": user_entity.get("username"),
        # Add more user properties as needed
    }

    # Generate a random number from 0 to 9 for the image filename
    random_number = random.randint(0, 9)
    image_filename = f"{random_number}.png"

    # Construct the URL with the bucket's public URL
    bucket_public_url = f"https://storage.cloud.google.com/{bucket_name}"
    image_url = f"{bucket_public_url}/{image_filename}"

    return render_template("user.html", username=username, user_info=user_info, image_url=image_url)



if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)

    # Ensure there are at least two user data entities in the database
    if count_users() < 2:
        # Add initial user data entities (you can change these values)
        initial_users = [
            {"username": "s3632442", "password": "abc123", "image_url": "user1.jpg"},
            {"username": "s3632443", "password": "bcd234", "image_url": "user2.jpg"}
        ]

        for user_data in initial_users:
            entity = datastore.Entity(key=datastore_client.key("user_data"))
            entity.update(user_data)
            datastore_client.put(entity)

