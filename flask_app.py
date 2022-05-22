from flask import Flask, render_template
import map_plotting_test as mpt

app = Flask(__name__)


@app.route('/')
def render_the_map():
    mpt.create_map()
    return render_template("map.html")


if __name__ == '__main__':
    app.run(debug=True)
