from dash import html, dcc, Input, Output, callback
import dash_bootstrap_components as dbc
from utils.consts import *
import plotly.express as px

player_appearance_component = dbc.Card(
    dbc.CardBody([
        dcc.Graph(id="appearances-graph")
    ]),
    className="m-2"
)


@callback(
    Output("appearances-graph", "figure"),
    Input("player-dropdown", "value")
)
def update_minutes_played(selected_player_id):
    if selected_player_id is None:
        return {}

    # Filter the appearances data for the selected player
    player_appearances = appearances_df[appearances_df["player_id"] == selected_player_id]
    if player_appearances.empty:
        return px.line(title="No appearance history available for this player.")

    # Sort data by date for proper chronological plotting
    player_appearances = player_appearances.sort_values("date")

    # Create the line plot
    fig = px.line(
        player_appearances,
        x="date",
        y="minutes_played",
        title=f"Minutes Played Over Time for {players_df[players_df['player_id'] == selected_player_id]['name'].values[0]}",
        labels={"date": "Date", "minutes_played": "Minutes Played"},
        markers=True
    )

    # Customize hover information to include additional events like red/yellow cards, goals, assists
    fig.update_traces(
        marker=dict(size=8, symbol="circle"),
        hovertemplate=(
            "<b>Date:</b> %{x}<br>"
            "<b>Minutes Played:</b> %{y}<br>"
            "<b>Goals:</b> %{customdata[0]}<br>"
            "<b>Assists:</b> %{customdata[1]}<br>"
            "<b>Yellow Cards:</b> %{customdata[2]}<br>"
            "<b>Red Cards:</b> %{customdata[3]}"
        ),
        customdata=player_appearances[["goals", "assists", "yellow_cards", "red_cards"]].values
    )

    # Customize layout
    fig.update_layout(yaxis_title="Minutes Played", xaxis_title="Date")

    return fig