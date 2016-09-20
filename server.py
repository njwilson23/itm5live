from flask import Flask, url_for

app = Flask("itmplots")

@app.route("/")
def root():
    u = url_for("static", filename="chart_bokeh.html")
    return u

@app.route("/itm5")
def itm5():
    return ("itm5")

if __name__ == "__main__":
    app.run()
