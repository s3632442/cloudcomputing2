# import datetime
# from flask import Flask, render_template
# app = Flask(__name__)
# @app.route("/")
# def root():
#  # For the sake of example, use static information to inflatethe template.
#  # This will be replaced with real information in later steps.
#  dummy_times = [
#  datetime.datetime(2018, 1, 1, 10, 0, 0),
#  datetime.datetime(2018, 1, 2, 10, 30, 0),
#  datetime.datetime(2018, 1, 3, 11, 0, 0),
#  ]
#  return render_template("index.html", times=dummy_times)
# if __name__ == "__main__":
#  app.run(host="127.0.0.1", port=8080, debug=True)

from google.cloud import datastore
import datetime
from flask import Flask, render_template

app = Flask(__name__)
datastore_client = datastore.Client()


def store_time(dt):
    entity = datastore.Entity(key=datastore_client.key("visit"))
    entity.update({"timestamp": dt})
    datastore_client.put(entity)


def fetch_times(limit):
    query = datastore_client.query(kind="visit")
    query.order = ["-timestamp"]
    times = query.fetch(limit=limit)
    return times


@app.route("/")
def root():
    # Store the current access time in Datastore.
    store_time(datetime.datetime.now(tz=datetime.timezone.utc))
    # Fetch the most recent 10 access times from Datastore.
    times = fetch_times(10)
    return render_template("index.html", times=times)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
