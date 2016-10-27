import os
import json
import database
import flask

app = flask.Flask("itm5live", static_url_path="")

@app.route("/")
def root():
    return flask.send_file("static/index.html")

@app.route("/map.html")
def map():
    return flask.send_file("static/map.html")

@app.route("/static/<path:filename>")
def send_static(filename):
    return flask.send_from_directory("static", filename)

@app.route("/images/<path:filename>")
def send_image(filename):
    return flask.send_from_directory("images", filename)

@app.route("/css/<path:filename>")
def css(filename):
    return flask.send_from_directory("css", filename)

@app.route("/js/<path:filename>")
def js(filename):
    return flask.send_from_directory("js", filename)

@app.route("/data/<path:filename>")
def send_data(filename):
    files = {
        "mc1.json" : {
            "table": "itm5",
            "fields": ["date AT TIME ZONE 'UTC'", "mc1temperature", "mc1salinity", "mc1pressure"],
            "retfields": ["date", "temperature", "salinity", "pressure"]
        },
        "mc2.json": {
            "table": "itm5",
            "fields": ["date AT TIME ZONE 'UTC'", "mc2temperature", "mc2salinity", "mc2pressure"],
            "retfields": ["date", "temperature", "salinity", "pressure"]
        },
        "mc3.json": {
            "table": "itm5",
            "fields": ["date AT TIME ZONE 'UTC'", "mc3temperature", "mc3salinity", "mc3pressure"],
            "retfields": ["date", "temperature", "salinity", "pressure"]
        },
        "mc4.json": {
            "table": "itm5",
            "fields": ["date AT TIME ZONE 'UTC'", "mc4temperature", "mc4salinity", "mc4pressure"],
            "retfields": ["date", "temperature", "salinity", "pressure"]
        },
        "aq1.json" : {
            "table": "itm5",
            "fields": ["date AT TIME ZONE 'UTC'", "ad1temperature", "ad1pressure", "ad1north", "ad1east", "ad1up"],
            "retfields": ["date", "temperature", "pressure", "north", "east", "up"]
        },
        "aq2.json": {
            "table": "itm5",
            "fields": ["date AT TIME ZONE 'UTC'", "ad2temperature", "ad2pressure", "ad2north", "ad2east", "ad2up"],
            "retfields": ["date", "temperature", "pressure", "north", "east", "up"]
        },
        "aq3.json": {
            "table": "itm5",
            "fields": ["date AT TIME ZONE 'UTC'", "ad3temperature", "ad3pressure", "ad3north", "ad3east", "ad3up"],
            "retfields": ["date", "temperature", "pressure", "north", "east", "up"]
        },
        "aq4.json": {
            "table": "itm5",
            "fields": ["date AT TIME ZONE 'UTC'", "ad4temperature", "ad4pressure", "ad4north", "ad4east", "ad4up"],
            "retfields": ["date", "temperature", "pressure", "north", "east", "up"]
        },
        "positions.json": {
            "table": "geo_itm5",
            "fields": ["date AT TIME ZONE 'UTC'", "longitude", "latitude"],
            "retfields": ["date", "longitude", "latitude"]
        }
    }

    params = files.get(filename, None)
    if params is None:
        flash.abort(404)

    return json.dumps(database.extract(params["table"], params["fields"],
                                       retfields=params.get("retfields", None)))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
