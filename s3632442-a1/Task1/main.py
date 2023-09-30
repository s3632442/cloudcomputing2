from werkzeug.datastructures import FileStorage
import time
import datetime
import socket
import os
import re
from flask import Flask, request, render_template, redirect, url_for, session
from google.cloud import datastore
from werkzeug.utils import secure_filename
from google.cloud import storage
from flask import send_from_directory

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

initialized = False

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

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def store_message(datastore_client, username, subject, message_text, image_url):
    print("46 store_message Image URL:", image_url)
    # Create an incomplete key with the kind 'message'
    key = datastore_client.key("message")

    # Create a new entity with the incomplete key
    entity = datastore.Entity(key=key)

    entity.update(
        {
            "user_message": message_text,
            "timestamp": datetime.datetime.now(tz=datetime.timezone.utc),
            "username": username,
            "subject": subject,
            "image_url": image_url,
        }
    )

    datastore_client.put(entity)



def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Modify the save_image function to store images in the Google Cloud Storage bucket
def save_image(file, image_reference):
    if file and allowed_file(file.filename):
        # Construct the object name in the bucket
        object_name = f"images/{image_reference}"

        # Upload the image to Google Cloud Storage
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(object_name)
        blob.upload_from_string(file.read(), content_type=file.content_type)

        # Return the public URL of the uploaded image
        image_url = blob.public_url
        print("82 save image Image URL:", image_url)
        return image_url

    return None


# @app.route("/", methods=["GET", "POST"])
# def login():
#     error_message = ""

#     if request.method == "POST":
#         username = request.form["username"]
#         password = request.form["password"]
#         id = request.form["id"]

#         # Check if the provided username and ID exist in the user_data entity kind
#         query = datastore_client.query(kind="user_data")
#         query.add_filter("username", "=", username)
#         query.add_filter("id", "=", id)
#         user_entities = query.fetch(limit=1)  # Use limit to fetch a single result

#         user_entity = next(user_entities, None)  # Get the first result or None if not found

#         if not user_entity:
#             # Username, ID, or password is incorrect (generic error message)
#             error_message = "Username, ID, or password is incorrect. Please try again."
#         else:
#             stored_password = user_entity.get("password")

#             # Check if the provided password matches the stored password
#             if password == stored_password:
#                 session["username"] = username
#                 return redirect(url_for("forum"))

#             # If the password is incorrect (generic error message)
#             error_message = "Username, ID, or password is incorrect. Please try again."

#     return render_template("login.html", error_message=error_message)


#####################################################
@app.route("/", methods=["GET", "POST"])
def login():
    error_message = ""

    # Fetch all user credentials for debugging (remove this in production)
    user_credentials = fetch_all_user_credentials()

    if request.method == "POST":
        id = request.form["id"]
        password = request.form["password"]

        # Check if the provided ID exists in the user_data entity kind
        query = datastore_client.query(kind="user_data")
        query.add_filter("id", "=", id)
        user_entities = query.fetch(limit=1)  # Use limit to fetch a single result

        user_entity = next(user_entities, None)  # Get the first result or None if not found

        if not user_entity:
            # ID or password is incorrect (generic error message)
            error_message = "ID or password is incorrect. Please try again."
            print("User not found. ID:", id, "Password:", password)  # Debugging statement
        else:
            stored_password = user_entity.get("password")

            # Check if the provided password matches the stored password
            if password == stored_password:
                session["id"] = id  # Store the authenticated ID in the session
                session["username"] = user_entity.get("username")  # Store the authenticated username in the session
                print("User successfully logged in. ID:", session["id"], "Username:", session["username"])  # Debugging statement
                return redirect(url_for("forum"))

            # If the password is incorrect (generic error message)
            error_message = "ID or password is incorrect. Please try again."
            print("Password incorrect for user with ID:", id)  # Debugging statement

    return render_template("login.html", error_message=error_message, user_credentials=user_credentials)




# Debugging function to fetch all user credentials (remove in production)
def fetch_all_user_credentials():
    query = datastore_client.query(kind="user_data")
    user_credentials = []

    for user_entity in query.fetch():
        user_id = user_entity.get("id")
        username = user_entity.get("username")
        password = user_entity.get("password")

        user_credentials.append(f"ID: {user_id}, Username: {username}, Password: {password}")

    return user_credentials

##########################################################
@app.route("/forum", methods=["GET", "POST"])
def forum():
    if "id" not in session:
        return redirect(url_for("login"))

    ds = datastore.Client()
    
    user_images = {}  # Initialize the user_images dictionary here

    if request.method == "POST":
        subject = request.form["subject"]
        message_text = request.form["message"]

        if "image" in request.files:
            image_file = request.files["image"]
            # Generate a unique image reference based on username and a timestamp
            image_reference = f"{session['username']}/{int(time.time())}.png" 
            image_url = save_image(image_file, image_reference) 
            print("197  forum  Image URL:", image_url)
        else:
            image_url = None

        store_message(datastore_client, session["username"], subject, message_text, image_url, image_reference)

    query = ds.query(kind="message", order=("-timestamp",))

    messages = []

    for message_entity in query.fetch(limit=10):
        user_message = message_entity.get("user_message", "Message content not found.")
        username = message_entity.get("username", "Unknown User")
        subject = message_entity.get("subject", "No Subject")
        image_reference = message_entity.get("image_reference", None)

        if image_reference:
            if '_' in image_reference:
                _, image_reference = image_reference.split('_', 1)  # Remove underscore and anything in front of it
            # Construct the image URL using the image reference
            image_url = f"https://storage.cloud.google.com/{bucket_name}/images/{image_reference}"
            print("219 route Image URL:", image_url)
        else:
            image_url = None

        messages.append({"username": username, "subject": subject, "message": user_message, "image_url": image_url})
    print("224 forum Image URL:", image_url)
    return render_template("forum.html", id=session["id"], messages=messages, user_images=user_images)



@app.route("/register", methods=["GET", "POST"])
def register():
    id_error = ""
    username_error = ""
    password_error = ""
    
    if request.method == "POST":
        id = request.form["id"]
        username = request.form["username"]
        password = request.form["password"]
        image_file = request.files["image"]

        if not id or not username or not password:
            if not id:
                id_error = "ID is required."
            if not username:
                username_error = "Username is required."
            if not password:
                password_error = "Password is required."
        else:
            username_exists = validate_username_exists(username)
            if username_exists:
                username_error = "Username already exists. Please choose a different username."

            password_requirements = validate_password_requirements(password)
            if not password_requirements:
                password_error = "Password must contain at least one letter, one number, one capital letter, and one special character."

            if not username_error and not password_error:
                if validate_id_and_username(id, username):
                    store_registration_data(id, username, password, image_file)
                    return render_template("registration_successful.html")
                else:
                    return render_template("invalid_id_username.html")

    return render_template("register.html", id_error=id_error, username_error=username_error, password_error=password_error)

def validate_password_requirements(password):
    # Password must contain at least one letter, one number, one capital letter, and one special character.
    return re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]+$', password) is not None

def validate_username_exists(username):
    # Initialize the Datastore client
    datastore_client = datastore.Client()

    # Query the Datastore to check if the username already exists
    query = datastore_client.query(kind="user_data")
    query.add_filter("username", "=", username)

    # Execute the query and check if any results are returned
    result = list(query.fetch())

    # If there are no results, the username is unique and valid
    return bool(result)  # True if username exists, False otherwise

def validate_id_and_username(id, username):
    if not id or not username:
        return False

    if not re.match(r'^[a-zA-Z0-9_-]+$', id) or not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False

    datastore_client = datastore.Client()
    query = datastore_client.query(kind="user_data")
    query.add_filter("id", "=", id)
    query.add_filter("username", "=", username)
    result = list(query.fetch())
    return not bool(result)

def store_registration_data(id, username, password, image_file):
    datastore_client = datastore.Client()
    storage_client = storage.Client()
    bucket_name = 'exampleapp-398810.appspot.com'

    filename = secure_filename(image_file.filename)
    object_name = f"images/{filename}"

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(object_name)
    blob.upload_from_string(image_file.read(), content_type=image_file.content_type)

    image_url = blob.public_url

    entity = datastore.Entity(key=datastore_client.key("user_data"))
    entity.update({
        "id": id,
        "username": username,
        "password": password,
        "image_url": image_url,
    })

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

    # Extract the number at the end of the username
    user_number = re.search(r'\d+$', username).group(0)

    # Construct the image URL based on the extracted number
    image_filename = f"{user_number}.png"
    image_url = f"https://storage.cloud.google.com/{bucket_name}/{image_filename}"
    print("349 route Image URL:", image_url)

   # Query the Datastore for the user's posts, including message body
    query = datastore_client.query(kind="message")
    query.add_filter("username", "=", username)
    user_posts = list(query.fetch())  # Use fetch() to get all user posts

    # Debugging: Print the message body for each message
    for message in user_posts:
        print("Message Body:", message.get("user_message"))

    # Fetch user images for the user posts
    user_images = {}  # Initialize the user_images dictionary here
    forum_images = {}  # Initialize the user_images dictionary here

    for message in user_posts:
        if message["username"]:
            # Extract the number at the end of the username
            user_number_match = re.search(r'\d+$', message["username"])
            user_number = user_number_match.group(0) if user_number_match else ""

            # Construct the image URL based on the extracted number
            image_filename = f"{user_number}.png"
            user_image_url = f"https://storage.cloud.google.com/{bucket_name}/{image_filename}"
            print("372 user Image URL:", image_url)
            user_images[message["username"]] = user_image_url  # Store the constructed image URL in the dictionary
            
            image_reference = message["image_reference"]
            print("377 forum Image URL:", image_reference)
            timestamp = message["timestamp"]
            print("377 forum Image URL:", image_reference)
            print("380 forum Image URL:", timestamp)

            # Construct the image URL based on the extracted number
            forum_image_url = f"https://storage.cloud.google.com/{bucket_name}/images/{image_reference}"
            print("384 forum Image URL:", image_url)
            forum_images[message["timestamp"]] = forum_image_url  # Store the constructed image URL in the dictionary

    return render_template("user.html", username=username, user_info=user_info, image_url=image_url, user_posts=user_posts,  forum_images=forum_images)


def store_message(datastore_client, username, subject, message_text, image_file, image_reference):
    # Create an incomplete key with the kind 'message'
    key = datastore_client.key("message")

    # Create a new entity with the incomplete key
    entity = datastore.Entity(key=key)

    entity.update(
        {
            "user_message": message_text,
            "timestamp": datetime.datetime.now(tz=datetime.timezone.utc),
            "username": username,
            "subject": subject,
            "image_reference": image_reference,  # Store the image reference
        }
    )

    if image_file:
        # Save the uploaded image with the provided image reference in its title
        save_image(image_file, image_reference)

    datastore_client.put(entity)


def save_image(file, image_reference):
    if file and isinstance(file, FileStorage) and allowed_file(file.filename):
        # Construct the object name with the provided image reference
        object_name = f"images/{image_reference}"

        # Upload the image to Google Cloud Storage
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(object_name)
        blob.upload_from_string(file.read(), content_type=file.content_type)

        # Return the public URL of the uploaded image
        image_url = blob.public_url
        print("414 save_image Image URL:", image_url)
        return image_url

    return None




@app.route("/edit_message/<int:message_id>", methods=["GET", "POST"])
def edit_message(message_id):
    if "id" not in session:
        return redirect(url_for("login"))

    # Fetch the message entity from the datastore
    message_key = datastore_client.key("message", message_id)
    message_entity = datastore_client.get(message_key)

    if not message_entity:
        return "Message not found", 404

    if request.method == "POST":
        # Get the new subject and message content from the form
        new_subject = request.form["new_subject"]
        new_message = request.form["new_message"]

        # Update the message entity with the new subject and message content
        message_entity["subject"] = new_subject
        message_entity["user_message"] = new_message
        datastore_client.put(message_entity)

        # Redirect to the forum page after updating the message
        return redirect(url_for("forum"))

    # Render the "Edit Message" page with the original message data
    return render_template("edit_message.html", message=message_entity, username=session["username"])



@app.route("/change_password", methods=["POST"])
def change_password():
    if "id" not in session:
        return redirect(url_for("login"))

    old_password = request.form["old_password"]
    new_password = request.form["new_password"]

    # Fetch the user entity from the datastore
    query = datastore_client.query(kind="user_data")
    query.add_filter("id", "=", session["id"])
    user_entity = next(query.fetch(limit=1), None)

    if not user_entity:
        return "User not found", 404

    stored_password = user_entity.get("password")

    if old_password != stored_password:
        # The old password is incorrect, so render the user page with an error message
        user_number = re.search(r'\d+$', session["username"]).group(0)
        image_filename = f"{user_number}.png"
        image_url = f"https://storage.cloud.google.com/{bucket_name}/{image_filename}"
        print("475 change password Image URL:", image_url)
        return render_template("user.html", username=session["username"], image_url=image_url, message="The old password is incorrect.")

    # Update the password in the datastore
    user_entity["password"] = new_password
    datastore_client.put(user_entity)

    # Redirect to the user page after changing the password
    return redirect(url_for("user", username=session["username"]))


@app.route("/reset_datastore")
def reset_datastore():
    # Delete all entities from the 'user_data' kind
    delete_all_entities("user_data")

    # Insert the new entities
    insert_initial_users()

    return "Datastore reset successfully."

def delete_all_entities():
    query = datastore_client.query(kind="user_data")
    entities = list(query.fetch())
    
    for entity in entities:
        datastore_client.delete(entity.key)


def insert_initial_users():
    new_entities = []

    for i in range(10):
        user_id = f"s3632442{i + 20}"
        username = f"Thomas{i} Lambert{i}"
        
        # Generate the password using a loop
        password = "".join(str(j % 10) for j in range(i, i + 6))
        
        image_url = f"user{i}.jpg"
        
        entity_data = {
            "id": user_id,
            "username": username,
            "password": password,
            "image_url": image_url,
        }

        new_entities.append(entity_data)

    for entity_data in new_entities:
        entity = datastore.Entity(key=datastore_client.key("user_data"))
        entity.update(entity_data)
        datastore_client.put(entity)

def reset_users():
    # Delete all entities from the 'user_data' kind
    delete_all_entities("user_data")

    # Insert ten new user entities
    for i in range(10):
        user_id = f"s3632442{i + 20}"
        username = f"Thomas{i} Lambert{i}"
        
        # Generate the password using a loop
        password = "".join(str(j % 10) for j in range(i, i + 6))
        
        image_url = f"user{i}.jpg"
        
        entity_data = {
            "id": user_id,
            "username": username,
            "password": password,
            "image_url": image_url,
        }

        datastore_client.put(datastore.Entity(key=datastore_client.key("user_data"), **entity_data))
    
def reset_users():
        delete_all_entities()  # Delete all existing entities
        insert_initial_users()  # Insert new entities with specific values

if initialized == False:
    reset_users()
    initialized = False

if __name__ == "__main__":

    app.run(host="127.0.0.1", port=8080, debug=True)

