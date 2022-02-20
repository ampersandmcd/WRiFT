from flask import render_template, request
from flask import current_app as app
import pandas as pd
import json
import plotly
import plotly.express as px
import plotly.graph_objects as go
import xarray as xr
from matplotlib.cm import viridis

token = open("../flask/application/static/.mapbox_token").read()
px.set_mapbox_access_token(token)


@app.route("/")
def index():
    #
    # render plotly demo plot
    # https://towardsdatascience.com/web-visualization-with-plotly-and-flask-3660abf9c946
    #
    # df = pd.DataFrame({
    #     "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
    #     "Amount": [4, 1, 2, 2, 4, 5],
    #     "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
    # })
    # fig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")
    # graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    #
    # render wildfire outline plot
    # https://community.plotly.com/t/plot-a-shapefile-shp-in-a-choropleth-chart/27850
    #
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
    # render scatterplot from downsampled netcdf
    # https://plotly.com/python/scatter-plots-on-maps/
    #
    # df = pd.read_csv("application/static/farsite_lonlat_low.csv")
    # fig = px.scatter_mapbox(df, lat="y", lon="x", color="US_ASP", opacity=0.1)
    # fig.update_layout(mapbox_style="satellite-streets")
    # fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    # graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    #
    # render toggleable layer scatterplot from downsampled netcdf
    # https://community.plotly.com/t/adding-multiple-layers-in-mapbox/25408
    # https://plotly.com/python/custom-buttons/
    #
    df = pd.read_csv("application/static/farsite_lonlat_low.csv")

    # add fake fire data
    distance_sq = (df["y"] - 37.307060)**2 + (df["x"] + 122.086650)**2
    df["FIRE"] = 0
    df.loc[distance_sq < 0.01, "FIRE"] = 1

    # add fake risk data
    df["RISK"] = df["US_210CC"]

    # generate layout for Plotly
    layout = go.Layout(mapbox=dict(accesstoken=token, center=dict(lat=df["y"].mean(), lon=df["x"].mean()), zoom=7),
                       height=550,
                       margin=dict(l=10, r=10, b=10, t=10))
    layout.update(mapbox_style="satellite-streets")


    # load data
    data = []
    display_columns = ["US_210CBD", "US_210CBH", "US_210CC", "US_210CH", "US_210EVC", "US_210EVH", "US_210F40",
                       "US_210FVC", "US_210FVH", "US_210FVT", "US_ASP", "US_DEM", "US_FDIST", "US_SLP", "RISK", "FIRE"]
    for column in display_columns:
        data.append(
            go.Scattermapbox(lat=df["y"], lon=df["x"], mode="markers", opacity=0.1, visible=False,
                             marker=dict(
                                 size=8,
                                 colorscale="viridis",
                                 color=df[column],
                                 colorbar_title=column,
                                 colorbar=dict(
                                     titleside="right",
                                 )
                             ),
                             hovertemplate=f"{column}: " + "%{marker.color}<br>" +
                                           "longitude: %{lon}<br>" +
                                           "latitude: %{lat}<br>" +
                                           "<extra></extra>"
                             )
        )
    data[0].visible = True

    # Create button list
    buttons = []
    for i, item in enumerate(display_columns):
        visibility = [False] * len(display_columns)
        visibility[i] = True
        buttons.append(dict(
            args=["visible", visibility],
            label=item,
            method="restyle"
        ))

    # Add mapbox and dropdown
    layout.update(
        updatemenus=[
            dict(
                buttons=buttons,
                direction="down",
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.1,
                xanchor="left",
                y=1.1,
                yanchor="top"
            ),
        ]
    )

    # Add annotation
    layout.update(
        annotations=[
            dict(text="Data Layer:", showarrow=False, x=0, y=1.05, yref="paper", align="left")
        ]
    )

    fig = go.Figure(data=data, layout=layout)
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


@app.route('/prototyping/', methods=['POST', 'GET'])
def prototyping():
    if request.method == 'GET':
        return f"The URL /data is accessed directly. Try going to '/form' to submit form"
    if request.method == 'POST':
        form_data = request.form
        return render_template('prototyping.html', form_data=form_data)
