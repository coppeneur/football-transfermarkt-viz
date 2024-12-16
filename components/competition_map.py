from dash import html, dcc, Input, Output, callback, dash_table
import dash_bootstrap_components as dbc
from utils.consts import *
import pandas as pd
import plotly.express as px
from utils.utilsFunctions import get_competition_name

# Define ISO3 country codes
countries = ["Denmark", "Spain", "France", "Italy", "Netherlands", "Portugal", "England", "Ukraine",
             "Greece", "Turkey", "Germany", "Russia", "Scotland", "Belgium"]
iso3_codes = ["DNK", "ESP", "FRA", "ITA", "NLD", "PRT", "GBR", "UKR", "GRC", "TUR", "DEU", "RUS", "GBR", "BEL"]
competition_ids = ["DK1", "ES1", "FR1", "IT1", "NL1", "PO1", "GB1", "UKR1", "GR1", "TR1", "L1", "RU1", "SC1", "BE1"]

# Create a dataframe for the map
map_data = pd.DataFrame({"Country": countries, "ISO3": iso3_codes, "CompetitionID": competition_ids})
map_data["CompetitionName"] = map_data["CompetitionID"].apply(get_competition_name)

competition_map_component = dbc.Card(
    [
        dbc.CardHeader("Map Highlighting the Country of the Selected Competition", className="text-center"),
        dbc.CardBody([
            dcc.Graph(id="competition-map", config={"displayModeBar": False})
        ]),
    ],
    className="m-2"
)


@callback(
    Output("competition-map", "figure"),
    Input("competition-dropdown", "value")
)
def update_competition_map(dropdown_value):
    # Initialize variables
    selected_competition_id = dropdown_value
    country_selected = None

    # Update country_selected based on the current competition ID
    if selected_competition_id is not None and not map_data[map_data["CompetitionID"] == selected_competition_id].empty:
        country_selected = map_data.loc[map_data["CompetitionID"] == selected_competition_id, "ISO3"].values[0]

    # Create the map figure
    fig = px.choropleth(
        map_data,
        locations="ISO3",
        locationmode="ISO-3",
        color_discrete_sequence=["#d3d3d3"],
        scope="europe",
        hover_data={"CompetitionName": True, "Country": True, "ISO3": False}  # Show CompetitionName and Country
    )

    fig.update_traces(
        hovertemplate=(
            "Competition: %{customdata[0]}<br>"  # Custom hover for CompetitionName
            "Country: %{customdata[1]}<br>"  # Custom hover for Country
        )
    )

    # Highlight the selected country
    if country_selected:
        fig.add_trace(
            px.choropleth(
                map_data[map_data["ISO3"] == country_selected],
                locations="ISO3",
                locationmode="ISO-3",
                color_discrete_sequence=["#636efa"],
                scope="europe",
                hover_data={"CompetitionName": True, "Country": True, "ISO3": False}  # Same hover data here
            ).data[0]
        )

    fig.update_geos(showcoastlines=True, coastlinecolor="Black", showland=True, landcolor="white")
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, uirevision="map", showlegend=False)  # Prevent map reset

    return fig


@callback(
    Output("competition-dropdown", "value"),
    Input("competition-map", "clickData")
)
def update_competition_dropdown(click_data):
    if click_data is None:
        return None

    selected_country = click_data["points"][0]["location"]
    selected_competition_id = map_data.loc[map_data["ISO3"] == selected_country, "CompetitionID"].values[0]

    return selected_competition_id
