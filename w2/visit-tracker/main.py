import datetime
from flask import Flask, render_template
app = Flask(__name__)
@app.route("/")
def root():
 # For the sake of example, use static information to inflatethe template.
 # This will be replaced with real information in later steps.
 dummy_times = [
 datetime.datetime(2018, 1, 1, 10, 0, 0),
 datetime.datetime(2018, 1, 2, 10, 30, 0),
 datetime.datetime(2018, 1, 3, 11, 0, 0),
 ]
 return render_template("index.html", times=dummy_times)
if __name__ == "__main__":
 app.run(host="127.0.0.1", port=8080, debug=True)