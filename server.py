"""
Server for itm5live
"""
import os
import datetime
import json
import flask
import pandas
import dateutil.parser
import database

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

def get_data(filename):
    files = {
        "mc1" : {
            "table": "itm5",
            "fields": ["date AT TIME ZONE 'UTC'", "mc1temperature", "mc1salinity", "mc1pressure"],
            "retfields": ["date", "temperature", "salinity", "pressure"]
        },
        "mc2": {
            "table": "itm5",
            "fields": ["date AT TIME ZONE 'UTC'", "mc2temperature", "mc2salinity", "mc2pressure"],
            "retfields": ["date", "temperature", "salinity", "pressure"]
        },
        "mc3": {
            "table": "itm5",
            "fields": ["date AT TIME ZONE 'UTC'", "mc3temperature", "mc3salinity", "mc3pressure"],
            "retfields": ["date", "temperature", "salinity", "pressure"]
        },
        "mc4": {
            "table": "itm5",
            "fields": ["date AT TIME ZONE 'UTC'", "mc4temperature", "mc4salinity", "mc4pressure"],
            "retfields": ["date", "temperature", "salinity", "pressure"]
        },
        "aq1" : {
            "table": "itm5",
            "fields": ["date AT TIME ZONE 'UTC'", "ad1temperature", "ad1pressure", "ad1north", "ad1east", "ad1up"],
            "retfields": ["date", "temperature", "pressure", "north", "east", "up"]
        },
        "aq2": {
            "table": "itm5",
            "fields": ["date AT TIME ZONE 'UTC'", "ad2temperature", "ad2pressure", "ad2north", "ad2east", "ad2up"],
            "retfields": ["date", "temperature", "pressure", "north", "east", "up"]
        },
        "aq3": {
            "table": "itm5",
            "fields": ["date AT TIME ZONE 'UTC'", "ad3temperature", "ad3pressure", "ad3north", "ad3east", "ad3up"],
            "retfields": ["date", "temperature", "pressure", "north", "east", "up"]
        },
        "aq4": {
            "table": "itm5",
            "fields": ["date AT TIME ZONE 'UTC'", "ad4temperature", "ad4pressure", "ad4north", "ad4east", "ad4up"],
            "retfields": ["date", "temperature", "pressure", "north", "east", "up"]
        },
        "positions": {
            "table": "geo_itm5",
            "fields": ["date AT TIME ZONE 'UTC'", "longitude", "latitude"],
            "retfields": ["date", "longitude", "latitude"]
        }
    }

    params = files.get(filename, None)
    if params is None:
        flask.abort(404)

    return database.extract(params["table"], params["fields"], retfields=params.get("retfields", None))

@app.route("/raw/<path:filename>")
def send_raw_data(filename):
    return json.dumps(get_data(filename))

def add_utc(d):
    return datetime.datetime(d.year, d.month, d.day, d.hour, d.minute, d.second,
                             tzinfo=datetime.timezone.utc)

@app.route("/data/<path:filename>")
def send_data(filename):
    try:
        timeResolution = int(flask.request.args.get("freqMinutes", 60))
    except ValueError:
        timeResolution = 60

    try:
        rawData = bool(flask.request.args.get("raw", 0))
    except ValueError:
        rawData = False

    try:
        smoothWin = int(flask.request.args.get("windowMinutes", 0))
    except ValueError as e:
        smoothWin = 0

    # load data from the database and parse a date index
    d = get_data(os.path.splitext(filename)[0])
    dateIndex = [add_utc(dateutil.parser.parse(a)) for a in d["date"]]
    referenceTime = datetime.datetime(2000, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
    d["timestamp"] = [(d-referenceTime).total_seconds() for d in dateIndex]
    del d["date"]

    df = pandas.DataFrame(data=d, index=dateIndex)

    # filter out bad MC4 data
    if not rawData:
        if filename.startswith("mc4"):
            df.salinity = df.salinity.apply(lambda x: x if x > 34.72 else None)

        #df.dropna(how="all", inplace=True)

    # resample by time
    if timeResolution > 60:
        df = df.resample("{0:d}T".format(round(timeResolution))).mean()

    # apply a moving window filter
    if smoothWin != 0:
        df = df.rolling("{0:d}T".format(smoothWin)).mean()
        #df = df.rolling(smoothWin, center=True).mean()

    if filename.endswith(".json"):
        return json.dumps(df.to_dict(orient="list")).replace("NaN", "null")
    elif filename.endswith(".csv"):
        return flask.Response(response=df.to_csv(), mimetype="text/csv")
    else:
        flask.abort(404)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
