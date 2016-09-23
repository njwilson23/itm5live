from flask import Flask, send_from_directory, send_file

app = Flask("itm5live", static_url_path="")

@app.route("/")
def root():
    return send_file("static/chart.html")

@app.route("/static/<path:filename>")
def send_static(filename):
    print(filename)
    return send_from_directory("static", filename)

@app.route("/data/<path:filename>")
def send_data(filename):
    return send_from_directory("static/data", filename)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
