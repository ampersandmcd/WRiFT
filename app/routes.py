from flask import render_template, request
from flask import current_app as app
import pandas as pd
import json
import plotly
import plotly.express as px
import plotly.graph_objects as go
import math
from geopy.geocoders import Nominatim

from app.modeling.farsite import burn
from app.modeling.economic_impacts import EconomicImpactCalculator

token = open("app/static/.mapbox_token").read()
px.set_mapbox_access_token(token)

impactCalculator = EconomicImpactCalculator()

@app.route("/", methods=["POST", "GET"])
def index():

    if request.method == "GET":
        #
        # load homepage
        # render toggleable layer scatterplot from downsampled netcdf
        # https://community.plotly.com/t/adding-multiple-layers-in-mapbox/25408
        # https://plotly.com/python/custom-buttons/
        #
        # import data and scale to appropriate values
        df = pd.read_csv("app/data/farsite_lonlat_low_risk_pop_housing.csv")
        df["Risk"] /= df["Risk"].max()

        # add fake temperature, humidity, wind speed, wind direction data
        df["Temperature"] = (1 - df["US_DEM"])
        df["Humidity"] = df["Temperature"]
        df["WindSpeed"] = df["US_DEM"]
        df["WindDirection"] = df["US_ASP"]

        # generate layout for Plotly
        layout = go.Layout(mapbox=dict(accesstoken=token, center=dict(lat=df["y"].mean(), lon=df["x"].mean()), zoom=8),
                           height=1000, margin=dict(l=10, r=10, b=10, t=10))
        layout.update(mapbox_style="satellite-streets",
                      coloraxis_colorbar={"yanchor": "top", "y":1, "x":0, "ticks":"outside"})


        impacts_data = {}

        # load data
        data = []
        # display_columns = ["US_210CBD", "US_210CBH", "US_210CC", "US_210CH", "US_210EVC", "US_210EVH", "US_210F40",
        #                    "US_210FVC", "US_210FVH", "US_210FVT", "US_ASP", "US_DEM", "US_FDIST", "US_SLP", "RISK", "FIRE"]
        display_columns = ["Risk", "Population", "Housing", "Temperature", "Humidity", "WindSpeed", "WindDirection"]
        for column in display_columns:
            data.append(
                go.Scattermapbox(lat=df["y"], lon=df["x"], mode="markers", opacity=0.1, visible=False,
                                 marker=dict(
                                     size=8,
                                     # colorscale="viridis",
                                     color=df[column],
                                     colorbar_title=column,
                                     colorbar=dict(
                                         titleside="right",
                                     )
                                 ),
                                 hovertemplate=f"{column}: " + "%{marker.color}<br>" +
                                               "Latitude: %{lat}<br>" +
                                               "Longitude: %{lon}<br>" +
                                               "<extra></extra>",
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
        # layout.update(
        #     updatemenus=[
        #         dict(
        #             buttons=buttons,
        #             direction="down",
        #             pad={"r": 10, "t": 10},
        #             showactive=True,
        #             x=0.1,
        #             xanchor="left",
        #             y=1.08,
        #             yanchor="top"
        #         ),
        #     ]
        # )

        # Add annotation
        # layout.update(
        #     annotations=[
        #         dict(text="Data Layer:", showarrow=False, x=0, y=1.05, yref="paper", align="left")
        #     ]
        # )

        fig = go.Figure(data=data, layout=layout)
        graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        return render_template("index.html", graph_json=graph_json, impacts=False, num_damaged=0, num_destroyed=0, impacts_data=impacts_data)

    if request.method == "POST":
        #
        # run simulation and render output
        #
        form_data = request.form
        # df = burn(lat=float(form_data["lat"]), lon=float(form_data["lon"]),
        #           path_farsite="application/static/farsite.nc", path_fueldict="application/static/FUEL_DIC.csv", mins=500)
        df = burn(lat=float(form_data["lat"]), lon=float(form_data["lon"]))

        impactCalculator.process_fire(df)
        num_damaged = impactCalculator.num_damaged()
        num_destroyed = impactCalculator.num_destroyed()

        # TO DO @BEN
        impacts_data = compute_impacts(df, 1, form_data, num_damaged, num_destroyed)

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

        return render_template("index.html", graph_json=graph_json, impacts=True, num_damaged=num_damaged, num_destroyed=num_destroyed,  impacts_data=impacts_data)


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


def compute_impacts(df, run, form_data, damaged, destroyed):
    geolocator = Nominatim(user_agent="geoapiExercises")
    impacts_data = {}
    # Key names

    if (run):
        # health page
        # injury
        # death
        # hopital_bed
        # ICU_bed
        # nurses
        # doctors
        impacts_data["injury"] = math.ceil(len(df) * .005 + destroyed * .30 + damaged * .15)
        impacts_data["death"] = math.floor(impacts_data["injury"] / 60)
        impacts_data["hospital_bed"] = math.ceil(impacts_data["injury"] * .55);
        impacts_data["ICU_bed"] = math.floor(impacts_data["injury"]*.15);
        impacts_data["nurses"] = math.ceil(impacts_data["hospital_bed"]/5);
        impacts_data["doctors"] = math.ceil(impacts_data["hospital_bed"]/12);

        # demographic
        # cities
        # counties
        # districts
        # income
        # education
        # age
        # nonwhite
        #Latitude = "37.33145"
        #Longitude = "-121.8877"
        # geolocator.geocode(str(Latitude)+","+str(Longitude))
        Latitude = df.y[0]
        Longitude = df.x[0]
        location = geolocator.reverse(str(Latitude) + "," + str(Longitude))
        address = location.raw['address']
        city = address.get('city', 'N/A')
        if city == "N/A":
            city = address.get('town', 'N/A')
        if city == "N/A":
            city = address.get('hamlet', 'N/A')
        if city == "N/A":
            city = address.get('village', 'N/A')
        if city == "N/A":
            city = address.get('road', 'N/A')

        impacts_data["cities"] = city
        impacts_data["counties"] = address.get('county', 'N/A')
        impacts_data["districts"] = "N/A"
        impacts_data["income"] = "N/A"
        impacts_data["education"] = "N/A"
        impacts_data["age"] = "N/A"
        impacts_data["nonwhite"] = address

        # environment
        # acres : calculated by estimating each tile to be about .0003 degrees (1degree=69 miles)  so .02 miles
        # based upon tests, the boxes test to be around 1 per 2.35 acres. Lnegth is . Need to calculate area though instead of number of points
        # smoke
        # CO2
        # PM
        # https://learn.kaiterra.com/en/air-academy/california-wildfires-2020-wildfire-pm2.5
        # https://www.pnas.org/doi/10.1073/pnas.2106478118
        # https://fire.airnow.gov/#
        #https://www.space.com/wildfire-smoke-satellite-images-us-canada

        temp = 1 + float(form_data["tempSlider"]) / 100
        humidity = 1 + float(form_data["humiditySlider"]) / 100
        windSpeed = 1 + float(form_data["wndSpdSlider"]) / 100
        outpm = 50 * temp * humidity
        inpm = 10 * temp * humidity
        acres = round(len(df) * .48, 2)
        if acres < 5000:
            wildfireSmoke = acres * .05 * windSpeed + .5
        else:
            wildfireSmoke = acres * .003 * windSpeed + 250

        impacts_data["acres"] = acres
        impacts_data["smoke"] = round(wildfireSmoke, 2)
        impacts_data["CO2"] = round(impacts_data["acres"] * 26, 2)
        impacts_data["OutPM"] = round(outpm, 2)
        impacts_data["InPM"] = round(inpm, 2)

    # do your calculations @ben
    return impacts_data
