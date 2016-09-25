import os
import json
import database
import flask

app = flask.Flask("itm5live", static_url_path="")

@app.route("/")
def root():
    return flask.send_file("static/chart.html")

@app.route("/static/<path:filename>")
def send_static(filename):
    print(filename)
    return flask.send_from_directory("static", filename)

@app.route("/data/<path:filename>")
def send_data(filename):
    if filename == "mc1":
        fields = ["date", "mc1temperature", "mc1salinity", "mc1pressure"]
        retfields = ["date", "temperature", "salinity", "pressure"]
    elif filename == "mc2":
        fields = ["date", "mc2temperature", "mc2salinity", "mc2pressure"]
        retfields = ["date", "temperature", "salinity", "pressure"]
    elif filename == "mc3":
        fields = ["date", "mc3temperature", "mc3salinity", "mc3pressure"]
        retfields = ["date", "temperature", "salinity", "pressure"]
    elif filename == "mc4":
        fields = ["date", "mc4temperature", "mc4salinity", "mc4pressure"]
        retfields = ["date", "temperature", "salinity", "pressure"]
    elif filename == "ad1":
        fields = ["date", "ad1temperature", "ad1pressure", "ad1north", "ad1east", "ad1up"]
        retfields = ["date", "temperature", "pressure", "north", "east", "up"]
    elif filename == "ad2":
        fields = ["date", "ad2temperature", "ad2pressure", "ad2north", "ad2east", "ad2up"]
        retfields = ["date", "temperature", "pressure", "north", "east", "up"]
    elif filename == "ad3":
        fields = ["date", "ad3temperature", "ad3pressure", "ad3north", "ad3east", "ad3up"]
        retfields = ["date", "temperature", "pressure", "north", "east", "up"]
    elif filename == "ad4":
        fields = ["date", "ad4temperature", "ad4pressure", "ad4north", "ad4east", "ad4up"]
        retfields = ["date", "temperature", "pressure", "north", "east", "up"]
    else:
        flask.abort(404)
    return json.dumps(database.extract(fields, retfields))
    #return send_from_directory("static/data", filename)

if __name__ == "__main__":
    if not os.path.isdir("static/data"):
        os.makedirs("static/data")
    app.run(host='0.0.0.0', port=5000)
