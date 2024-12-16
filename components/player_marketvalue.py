from dash import html, dcc, Input, Output, callback
import dash_bootstrap_components as dbc
from plotly.graph_objs import Scatter

from utils.consts import *  # Ensure vibrant_colors is imported from this module
import plotly.express as px


# Position color map
def get_position_color(position):
    return position_color_map.get(position, "#636EFA")  # Default color if position not in map


player_marketvalue_component = dbc.Card(
    dbc.CardBody([
        dcc.Graph(id="market-valuation-graph", config={"displayModeBar": False})  # Graph placeholder
    ]),
    className="m-2"
)


@callback(
    Output("market-valuation-graph", "figure"),
    [
        Input("player-dropdown", "value"),
        Input('season-competition-dropdown', 'value'),
        Input('competition-dropdown', 'value'),
    ]
)
def update_valuation_graph(selected_player_id, selected_season_id, selected_competition_id):
    if selected_player_id is None:
        # Return an empty figure if no player is selected
        return {}

    # Filter the data for the selected player
    player_data = player_valuations_df[player_valuations_df["player_id"] == selected_player_id]

    # Get the player's name and position
    player_row = players_df[players_df['player_id'] == selected_player_id]
    player_name = player_row['name'].values[0]
    player_position = player_row['position'].values[0]

    # Determine the line color based on the player's position
    line_color = get_position_color(player_position)

    # Convert season start and end dates to datetime
    seasons_df["start"] = pd.to_datetime(seasons_df["start"])
    seasons_df["end"] = pd.to_datetime(seasons_df["end"])

    # Find the range of player valuation dates
    player_dates = pd.to_datetime(player_data["date"])
    valuation_start = player_dates.min()
    valuation_end = player_dates.max()

    # Filter seasons within the range of the player's valuation dates
    seasons_in_range = seasons_df[
        ((seasons_df["start"] <= valuation_end) & (seasons_df["end"] >= valuation_start) &
         (seasons_df["competition_id"] == selected_competition_id))
    ]

    # Add the current season if it falls outside the valuation range
    current_season = seasons_df[
        (seasons_df["season"] == selected_season_id) & (seasons_df["competition_id"] == selected_competition_id)
        ]

    if not current_season.empty:
        current_season_start = current_season.iloc[0]["start"]
        current_season_end = current_season.iloc[0]["end"]
        if (current_season_start > valuation_end) or (current_season_end < valuation_start):
            seasons_in_range = pd.concat([seasons_in_range, current_season]).drop_duplicates()

    # Create the line graph using Plotly Express
    fig = px.line(
        player_data,
        x="date",
        y="market_value_in_eur",
        title=f"Market Valuation of {player_name} Over Time",
        labels={"date": "Date", "market_value_in_eur": "Market Value"},
        markers=True,
    )

    # Update line color and layout
    fig.update_traces(line_color=line_color, name="Market Valuation")
    fig.update_layout(
        xaxis=dict(
            title="Date",
            showgrid=True,
            showline=True,
            zeroline=False
        ),
        yaxis=dict(
            title="Market Value",
            tickprefix="€",
            showgrid=True,
            showline=True,
            zeroline=False
        ),
        margin=dict(t=50, l=50, r=50, b=50),
    )

    # Add shaded background for the current season
    if not current_season.empty:
        fig.add_shape(
            type="rect",
            x0=current_season.iloc[0]["start"],
            x1=current_season.iloc[0]["end"],
            y0=0,
            y1=player_data["market_value_in_eur"].max(),
            fillcolor="rgba(255, 0, 0, 0.2)",
            line_width=0,
            layer="below",
            name="Current Season"
        )

    # Add vertical lines for season start and end
    for _, season_row in seasons_in_range.iterrows():
        season_start = season_row["start"]
        season_end = season_row["end"]

        # Add vertical line for season start
        fig.add_shape(
            type="line",
            x0=season_start,
            x1=season_start,
            y0=0,
            y1=player_data["market_value_in_eur"].max(),
            line=dict(color="gray", dash="dot"),
            name="Season Border",
        )

        # Add vertical line for season end
        fig.add_shape(
            type="line",
            x0=season_end,
            x1=season_end,
            y0=0,
            y1=player_data["market_value_in_eur"].max(),
            line=dict(color="gray", dash="dot"),
            name="Season Border",
        )

        # Add a dummy trace for "Marked Season"
    fig.add_trace(
        Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker=dict(size=10, color="rgba(255, 0, 0, 0.5)", symbol="square"),
            name="Current Season"
        )
    )

    # Add a dummy trace for "Season Boundaries"
    fig.add_trace(
        Scatter(
            x=[None],
            y=[None],
            mode="lines",
            line=dict(color="gray", dash="dot"),
            name="Season Boundaries"
        )
    )

    # Update the main line trace (Market Valuation) with legend visibility
    fig.update_traces(
        name="Market Valuation",
        showlegend=True
    )

    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255, 255, 255, 0.8)",
           # bordercolor="gray",
           # borderwidth=1
        ),
        margin=dict(t=120, l=50, r=50, b=50)  # Maintain margins for proper spacing
    )

    fig.update_traces(name="Current Season", selector=dict(mode="markers"))
    fig.update_traces(name="Season Start/End", selector=dict(mode="lines"))
    return fig
