from flask import render_template, request
from flask import current_app as app
import pandas as pd
import json
import plotly
import plotly.express as px
import xarray as xr


@app.route("/")
def index():
    #
    # load demo plot https://towardsdatascience.com/web-visualization-with-plotly-and-flask-3660abf9c946
    #

    df = pd.DataFrame({
        "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
        "Amount": [4, 1, 2, 2, 4, 5],
        "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
    })
    fig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")
    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    #
    # load wildfire plot
    #
    # with open(r"application/static/AgencyHistoricFirePerimeters_2020.json") as f:
    #     raw = f.read()
    # fires = json.loads(raw)
    # fires["features"] = fires["features"][:10]      # subset first 10 wildfires for now
    # fires["features"] = fires["features"]
    # df = pd.DataFrame([fires["features"][i]["properties"] for i in range(10)])
    # geojson = [fires["features"][i]["geometry"] for i in range(10)]
    # fig = px.choropleth_mapbox(data_frame=df, geojson=geojson, locations="GEO_ID", color="GIS_ACRES", featureidkey="GEO_ID",
    #                            color_continuous_scale="Viridis",
    #                            mapbox_style="carto-positron",
    #                            zoom=3, center={"lat": 37.0902, "lon": -95.7129},
    #                            opacity=0.5)
    # graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    #
    # load netCDF plot
    #
    df = pd.read_csv("application/static/farsite_lonlat_low.csv")
    fig = px.scatter_mapbox(df, lat="x", lon="y", color="US_210CBD")
    fig.update_layout(
        mapbox_style="white-bg",
        mapbox_layers=[
            {
                "below": 'traces',
                "sourcetype": "raster",
                "sourceattribution": "United States Geological Survey",
                "source": [
                    "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}"
                ]
            }
        ])
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template("index.html", graph_json=graph_json)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/problem")
def problem():
    return render_template("problem.html")


@app.route("/resources")
def resources():
    return render_template("resources.html")


@app.route("/solution")
def solution():
    return render_template("solution.html")

@app.route('/prototyping/', methods = ['POST', 'GET'])
def prototyping():
    if request.method == 'GET':
        return f"The URL /data is accessed directly. Try going to '/form' to submit form"
    if request.method == 'POST':
        form_data = request.form
        return render_template('prototyping.html',form_data = form_data)
