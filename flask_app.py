from flask import Flask, render_template
import map_plotting_module as mpm

app = Flask(__name__)


@app.route('/')
def loading():
    return render_template("loading.html")


@app.route('/map')
def show_map():
    return render_template("map.html")


@app.route('/create_map')
def create_map():
    mpm.create_map()
    return "Map created"


if __name__ == '__main__':
    app.run()
