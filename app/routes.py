import numpy as np
from flask import render_template, request, jsonify
from flask import current_app as app
import pandas as pd
import json
import random
import plotly
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff

from app.modeling.farsite import burn
from app.modeling.economic_impacts import EconomicImpactCalculator

token = open("app/static/.mapbox_token").read()
px.set_mapbox_access_token(token)

# from https://www.iii.org/article/facts-about-wildfires
fun_facts = [
    "Wildfires occur in 38 states; California is the state most associated with wildfires and, in fact, eight of the 10 most costly wildfires in the U.S. have occurred there. That said, Texas has been known to have twice the wildfires as California in a given year and 38 of U.S. states have areas at risk.",
    "Wildfires like dry conditions; drought conditions, dry undergrowth and the presence of combustible and flammable materials contribute to wildfire hazard.",
    "Wildfires are more dangerous in combination with development; the risk of damage increases as housing and business development expands into the wildfire-prone wildland-urban interface (WUI), such as mountain, foothill or grassland areas.",
    "Wildfires spread mostly due to wind; direct flame contact and radiant heat from a wildfire can ignite combustible materials. However, research has shown that homes burned during wildfires most frequently catch fire from live embers (or 'firebrands') that are blown by the wind.",
    "Wildfires thrive on house 'togetherness'; because of the dangers of the embers, close proximity of homes and presence of combustible features both increase the chances of a home going up in flames. Fire spreads rapidly when homes are less than 15 feet apart, making homes that are clustered near others more likely to burn. Features like fences and attached decks made from combustible materials often hasten the spread of fire."
]
prevention_facts = [
    "maintaining five feet of non-combustible 'defensible space' around your home; keep a five-foot diameter space of gravel, brick, or concrete in the area adjacent to your home.",
    "maintaining an expanded 'defensible space' between five and 30 feet from your home; keeping this area as unattractive to wildfires as possible will reduce the risk. Move trailers/RVs and storage sheds from area, or build defensible space (see above) around these items. Remove shrubs under trees, prune branches that overhang your roof, thin trees, and remove dead vegetation.",
    "using non-combustible siding and maintaining a six-inch ground-to-siding clearance.",
    "regularly cleaning from your roof and gutters to keep debris from being ignited by wind-blown embers. Use noncombustible gutter covers.",
    "getting a Class A fire-rated roof; Class A roofing products offer the best protection for homes.",
    "using non-combustible fences and gates; burning fencing can generate embers and cause direct flame contact to your home.",
    "covering vents and creating soffited eaves; use 1/8-inch mesh to cover vents, and box-in (create soffits) on open eaves to keep embers out.",
    "using multi-pane, tempered glass windows; close windows when a wildfire threatens.",
    "fireproofing the deck; at a minimum, use deck boards that comply with California requirements for new construction in wildfire-prone areas. Remove combustibles from under deck, and maintain effective defensible space around the deck.",
    "keeping combustibles far away from the house; combustible structures in the yard such as wood, plastic or plastic-wood playground equipment should be at least 30 feet away from the house. Experts indicate that evergreen trees, palms and eucalyptus trees have more combustible qualities than others—keep this type of vegetation 100 feet away from the house."
]

# load impacts data
impactCalculator = EconomicImpactCalculator()

# load raster data and scale to appropriate values
df = pd.read_pickle("app/data/risk_pop_housing.pickle")
df["Risk"] /= df["Risk"].max()

# add fake temperature, humidity, wind speed, wind direction data
df["Temperature"] = 0 * df["Risk"] + 70
df["Humidity"] = 0 * df["Risk"] + 20
df["WindSpeed"] = 0 * df["Risk"] + 10
df["WindDirection"] = 0 * df["Risk"] + 270

# load vector data
perimeters = pd.read_pickle("app/data/perimeters.pickle")


@app.route("/", methods=["POST", "GET"])
def index():

    if request.method == "GET":
        #
        # load homepage
        # render toggleable layer scatterplot from downsampled netcdf
        # https://community.plotly.com/t/adding-multiple-layers-in-mapbox/25408
        # https://plotly.com/python/custom-buttons/
        #
        global df
        global perimeters

        # generate layout for Plotly
        layout = go.Layout(mapbox=dict(accesstoken=token, center=dict(lat=df["y"].mean(), lon=df["x"].mean()), zoom=8),
                           height=1000, margin=dict(l=10, r=10, b=10, t=10))
        layout.update(mapbox_style="satellite-streets",
                      coloraxis_colorbar={"yanchor": "top", "y":1, "x":0, "ticks":"outside"})

        # render raster data
        data = []
        raster_columns = ["Risk", "Population", "Housing", "Temperature", "Humidity", "WindSpeed", "WindDirection"]
        for column in raster_columns:
            clims = {}
            # scatter plot
            if column in ["Population", "Housing"]:
                # rescale colorbar for population and housing data
                clims = dict(cmin=np.quantile(df[column], 0.05), cmax=np.quantile(df[column], 0.95))
            data.append(
                go.Scattermapbox(lat=df["y"], lon=df["x"], mode="markers", opacity=0.1, visible=False,
                                 marker=dict(
                                     size=8,
                                     color=df[column],
                                     colorbar_title=column,
                                     colorbar=dict(
                                         titleside="right",
                                     ),
                                     **clims
                                 ),
                                 hovertemplate=f"{column}: " + "%{marker.color}<br>" +
                                               "Latitude: %{lat}<br>" +
                                               "Longitude: %{lon}<br>" +
                                               "<extra></extra>",
                                 )
            )
        data[0].visible = True

        # render quiver data
        # quiver = ff.create_quiver(x=df["x"], y=df["y"],
        #                           u=np.cos(np.deg2rad(df["WindDirection"])),
        #                           v=np.sin(np.deg2rad(df["WindDirection"])),
        #                           visible=False,
        #                           marker=dict(
        #                               color=df["WindDirection"],
        #                               colorbar_title="Wind Direction",
        #                               colorbar=dict(titleside="right")
        #                           ),
        #                           hovertemplate=f"Wind Direction: " + "%{marker.color}<br>" +
        #                                         "Latitude: %{y}<br>" +
        #                                         "Longitude: %{x}<br>" +
        #                                         "<extra></extra>"
        #                           )
        # data.append(quiver.data)

        # render vector data
        data.append(
            go.Choroplethmapbox(geojson=perimeters.__geo_interface__,
                                visible=False,
                                marker=dict(
                                    opacity=0.8,
                                ),
                                locations=perimeters.index,
                                z=perimeters["YEAR_"],
                                colorbar_title="Year",
                                colorbar=dict(
                                    titleside="right",
                                ),
                                customdata=perimeters[["FIRE_NAME", "YEAR_", "ALARM_DATE", "CONT_DATE", "GIS_ACRES"]],
                                hovertemplate=f"Historical Fire<br>" +
                                       "Name: %{customdata[0]}<br>" +
                                       "Year: %{customdata[1]}<br>" +
                                       "Ignited: %{customdata[2]}<br>" +
                                       "Contained: %{customdata[3]}<br>" +
                                       "Acres: %{customdata[4]}<br>" +
                                       "<extra></extra>",
            )
        )

        fig = go.Figure(data=data, layout=layout)
        graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        return render_template("index.html", graph_json=graph_json, impacts=False,
                               num_damaged=0, num_destroyed=0,
                               fun_fact=random.choice(fun_facts),
                               prevention_fact=random.choice(prevention_facts))

    if request.method == "POST":
        #
        # run simulation and render output
        #
        form_data = request.form
        # df = burn(lat=float(form_data["lat"]), lon=float(form_data["lon"]),
        #           path_farsite="application/static/farsite.nc", path_fueldict="application/static/FUEL_DIC.csv", mins=500)
        df = burn(lat=float(form_data["lat"]), lon=float(form_data["lon"]))

        global impactCalculator
        impactCalculator.process_fire(df)
        num_damaged = impactCalculator.num_damaged()
        num_destroyed = impactCalculator.num_destroyed()

        # generate layout for Plotly
        layout = go.Layout(mapbox=dict(accesstoken=token, center=dict(lat=df["y"].mean(), lon=df["x"].mean()), zoom=12),
                           height=1000, margin=dict(l=10, r=10, b=10, t=10))
        layout.update(mapbox_style="satellite-streets")

        # load data
        data = []
        for fire in impactCalculator.get_fire_shape():
            data.append(
                go.Scattermapbox(lat=[p[1] for p in fire],
                                 lon=[p[0] for p in fire],
                                 marker=dict(size=0, color="orange"),
                                 fill="toself",
                                 name="Fire footprint"
                                 )
            )
        for building in impactCalculator.get_damaged_structure_shape():
            data.append(
                go.Scattermapbox(lat=[p[1] for p in building],
                                 lon=[p[0] for p in building],
                                 marker=dict(size=0, color="yellow"),
                                 fill="toself",
                                 name="Damaged structure"
                                 )
                )
        for building in impactCalculator.get_destroyed_structure_shape():
            data.append(
                go.Scattermapbox(lat=[p[1] for p in building],
                                 lon=[p[0] for p in building],
                                 marker=dict(size=0, color="red"),
                                 fill="toself",
                                 name="Destroyed structure"
                                 )
                )
        fig = go.Figure(data=data, layout=layout)
        graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        return render_template("index.html", graph_json=graph_json, impacts=True,
                               num_damaged=num_damaged, num_destroyed=num_destroyed,
                               fun_fact=random.choice(fun_facts),
                               prevention_fact=random.choice(prevention_facts))


@app.route("/background_historical", methods=["GET"])
def background_historical(date="2022-01-01"):
    # TODO: call Nathan's code here
    return jsonify({
        "Temperature": list(0 * df["Temperature"].values),
        "Humidity": list(0 * df["Humidity"].values),
        "WindSpeed": list(0 * df["WindSpeed"].values),
        "WindDirection": list(0 * df["WindDirection"].values)
    })

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


@app.route("/prototyping/", methods=["POST", "GET"])
def prototyping():
    if request.method == "GET":
        return f"The URL /data is accessed directly. Try going to '/form' to submit form"
    if request.method == "POST":
        form_data = request.form
        return render_template("prototyping.html", form_data=form_data)
