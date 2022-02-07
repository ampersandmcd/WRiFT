from flask import render_template, request
from flask import current_app as app
import pandas as pd
import json
import plotly
import plotly.express as px
import plotly.graph_objects as go
import xarray as xr

token = open("../flask/application/static/.mapbox_token").read()
px.set_mapbox_access_token(token)


@app.route("/")
def index():
    #
    # render demo plot https://towardsdatascience.com/web-visualization-with-plotly-and-flask-3660abf9c946
    #
    # df = pd.DataFrame({
    #     "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
    #     "Amount": [4, 1, 2, 2, 4, 5],
    #     "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
    # })
    # fig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")
    # graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    #
    # render wildfire plot
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
    # render plot from converted netcdf
    #
    df = pd.read_csv("application/static/farsite_lonlat_low.csv")
    fig = px.scatter_mapbox(df, lat="y", lon="x", color="US_DEM", opacity=0.1)
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

    #
    # render toggleable layer plot
    #
    # df = pd.read_csv("application/static/farsite_lonlat_low.csv")
    # layout = go.Layout(mapbox=dict(accesstoken=token, center=dict(lat=df["y"].mean(), lon=df["x"].mean()), zoom=3))
    # layout.update(
    #     mapbox_style="white-bg",
    #     mapbox_layers=[
    #         {
    #             "below": 'traces',
    #             "sourcetype": "raster",
    #             "sourceattribution": "United States Geological Survey",
    #             "source": [
    #                 "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}"
    #             ]
    #         }
    #     ]
    # )
    #
    # # load data
    # data = []
    # # display_columns = ["US_210CBD", "US_210CBH", "US_210CC", "US_210CH", "US_210EVC", "US_210EVH", "US_210F40",
    # #                    "US_210FVC", "US_210FVH", "US_210FVT", "US_ASP", "US_DEM", "US_FDIST", "US_SLP"]
    # display_columns = ["US_DEM", "US_SLP"]
    # for column in display_columns:
    #     data.append(
    #         go.Scattergeo(lat=df["y"], lon=df["x"], customdata=df, marker_color=df[column], opacity=0.1, visible=True)
    #     )
    # data[0].visible = True
    #
    # # Create button list
    # buttons = []
    # for i, item in enumerate(display_columns):
    #     visibility = [False] * len(display_columns)
    #     visibility[i] = True
    #     buttons.append(dict(
    #         args=["visible", visibility],
    #         label=item,
    #         method="restyle"
    #     ))
    #
    # # Add mapbox and dropdown
    # layout.update(
    #     mapbox=dict(accesstoken=token),
    #     updatemenus=[
    #         dict(
    #             buttons=buttons,
    #             direction="down",
    #             pad={"r": 10, "t": 10},
    #             showactive=True,
    #             x=0.1,
    #             xanchor="left",
    #             y=1.1,
    #             yanchor="top"
    #         ),
    #     ]
    # )
    #
    # # Add annotation
    # layout.update(
    #     annotations=[
    #         dict(text="Data Layer:", showarrow=False,
    #              x=0, y=1.085, yref="paper", align="left")
    #     ]
    # )
    #
    # fig = go.Figure(data=data, layout=layout)
    # graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

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


@app.route('/prototyping/', methods=['POST', 'GET'])
def prototyping():
    if request.method == 'GET':
        return f"The URL /data is accessed directly. Try going to '/form' to submit form"
    if request.method == 'POST':
        form_data = request.form
        return render_template('prototyping.html', form_data=form_data)
