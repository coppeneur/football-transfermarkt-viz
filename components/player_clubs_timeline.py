from dash import html, dcc, Input, Output, callback
import dash_bootstrap_components as dbc
from utils.consts import *
import plotly.express as px

player_clubs_timeline_component = dbc.Card(
    dbc.CardBody([
        dcc.Graph(id="clubs-timeline-graph")
    ]),
    className="m-2"
)


@callback(
    Output("clubs-timeline-graph", "figure"),
    Input("player-dropdown", "value")
)
def update_clubs_timeline(selected_player_id):
    if selected_player_id is None:
        return {}

    player_transfers = transfers_df[transfers_df["player_id"] == selected_player_id]

    if player_transfers.empty:
        return px.line(title="No transfer history available for this player.")

    player_transfers = player_transfers.sort_values("transfer_date")

    fig = px.line(
        player_transfers,
        x="transfer_date",
        y="to_club_name",
        title=f"Club History of {players_df[players_df['player_id'] == selected_player_id]['name'].values[0]}",
        labels={"transfer_date": "Transfer Date", "to_club_name": "Club"},
        markers=True
    )
    fig.update_traces(marker=dict(size=10, symbol="circle"))
    fig.update_layout(yaxis_title="Clubs", xaxis_title="Date")

    return fig
