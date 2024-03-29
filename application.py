import re, os
from flask import Flask, jsonify, render_template, request, url_for
from flask_jsglue import JSGlue

from sqlalchemy import create_engine
from helpers import lookup

# configure application
app = Flask(__name__)
JSGlue(app)

# configure CS50 Library to use SQLite database
db = create_engine("sqlite:///location.db")

@app.route("/")
def index():
    """Render map."""
    return render_template("index.html")

@app.route("/articles")
def articles():
    """Look up articles for geo."""
    
    g=request.args.get("geo")
    
    if not g:
        raise RuntimeError("Missing Loc")
    
    articles=lookup(g)
    
    if len(articles)<=5:
        return jsonify(articles)
    else:
        return jsonify([articles[0],articles[1],articles[2],articles[3],articles[4]])

@app.route("/search")
def search():
    """Search for places that match query."""

    q=request.args.get("q")+"%"
    result=db.engine.execute("SELECT * FROM places WHERE postal_code LIKE :q OR place_name LIKE :q OR admin_name1 LIKE :q", q=q)
    results = []

    for a in result:
        row = []
        for b in a:
            row.append(b)
        results.append(tuple(row))

    # print(jsonify(results))

    if len(results)<=10:
        return jsonify(results)
    else:
        return jsonify([results[0],results[1],results[2],results[3],results[4],results[5],results[6],results[7],results[8],results[9]])

@app.route("/update")
def update():
    """Find up to 10 places within view."""

    # ensure parameters are present
    if not request.args.get("sw"):
        raise RuntimeError("missing sw")
    if not request.args.get("ne"):
        raise RuntimeError("missing ne")

    # ensure parameters are in lat,lng format
    if not re.search("^-?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?$", request.args.get("sw")):
        raise RuntimeError("invalid sw")
    if not re.search("^-?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?$", request.args.get("ne")):
        raise RuntimeError("invalid ne")

    # explode southwest corner into two variables
    (sw_lat, sw_lng) = [float(s) for s in request.args.get("sw").split(",")]

    # explode northeast corner into two variables
    (ne_lat, ne_lng) = [float(s) for s in request.args.get("ne").split(",")]

    # find 10 cities within view, pseudorandomly chosen if more within view
    if (sw_lng <= ne_lng):

        # doesn't cross the antimeridian
        rows = db.engine.execute("""SELECT * FROM places
            WHERE :sw_lat <= latitude AND latitude <= :ne_lat AND (:sw_lng <= longitude AND longitude <= :ne_lng)
            GROUP BY country_code, place_name, admin_code1
            ORDER BY RANDOM()
            LIMIT 10""",
            sw_lat=sw_lat, ne_lat=ne_lat, sw_lng=sw_lng, ne_lng=ne_lng)

    else:

        # crosses the antimeridian
        rows = db.engine.execute("""SELECT * FROM places
            WHERE :sw_lat <= latitude AND latitude <= :ne_lat AND (:sw_lng <= longitude OR longitude <= :ne_lng)
            GROUP BY country_code, place_name, admin_code1
            ORDER BY RANDOM()
            LIMIT 10""",
            sw_lat=sw_lat, ne_lat=ne_lat, sw_lng=sw_lng, ne_lng=ne_lng)

    # output places as JSON
    results = []
    for a in rows:
        row = []
        for b in a:
            row.append(b)
        results.append(list(row))

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
