from dash import html, dcc, Input, Output, callback
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from utils.consts import *
from utils.utilsFunctions import *
import plotly.graph_objects as go
from utils.tol_colors import tol_cset

clubs_value_component = dbc.Card(
    dbc.CardBody([
        dcc.Dropdown(
            id="clubs-value-scope-dropdown",
            options=[
                {"label": "All Positions", "value": "all"},
                {"label": "Attack", "value": "Attack"},
                {"label": "Midfield", "value": "Midfield"},
                {"label": "Defender", "value": "Defender"},
                {"label": "Goalkeeper", "value": "Goalkeeper"},
            ],
            value="all",
        ),
        dcc.Store(id="club-stats-store"),
        dcc.Graph(id="clubs-value-graph")
    ]),
    className="m-2"
)


@callback(
    [Output("clubs-value-graph", "figure"),
     Output("club-stats-store", "data")],
    [
        Input("competition-dropdown", "value"),
        Input("season-competition-dropdown", "value"),
        Input("clubs-value-scope-dropdown", "value"),
        Input("rankings-data-store", "data")
    ]
)
def update_clubs_value_figure(selected_competition_id, selected_season, scope_value, rankings_data):
    if selected_competition_id is None or selected_season is None or rankings_data is None:
        return {}, []

    # Convert rankings data back to DataFrame
    ranking_df = pd.DataFrame(rankings_data)

    # Filter games based on selected competition and season
    filtered_games = games_df[
        (games_df["competition_id"] == selected_competition_id) &
        (games_df["season"] == selected_season)
        ]

    game_ids = filtered_games['game_id'].unique()

    # Get all club IDs from home and away matches
    home_club_ids = filtered_games['home_club_id']
    away_club_ids = filtered_games['away_club_id']
    all_club_ids = pd.concat([home_club_ids, away_club_ids]).unique()

    # Filter appearances for players in the selected games
    filtered_appearances = appearances_df[appearances_df['game_id'].isin(game_ids)]

    # Merge filtered appearances with player data
    player_data = filtered_appearances.merge(players_df, on="player_id", how="left")

    # Remove duplicate player entries for the same club
    player_data = player_data.drop_duplicates(subset=["player_id", "player_club_id"])

    player_data.rename(columns={'market_value_in_eur': 'market_value_in_eur_old'}, inplace=True)

    # Get market value data for the selected season
    market_values = get_player_market_value_by_season(player_data, selected_season, selected_competition_id)

    # Merge market values back into the player data
    player_data = player_data.merge(market_values, on="player_id", how="left")

    # Initialize results list
    results = []

    # Process each club
    for club_id in all_club_ids:
        club_players = player_data[player_data['player_club_id'] == club_id]

        # Calculate total market value
        total_value = club_players['market_value_in_eur'].sum()

        # Calculate club size (unique players)
        club_size = club_players['player_id'].nunique()

        # Calculate value by position
        position_values = club_players.groupby('position')['market_value_in_eur'].sum().to_dict()

        # Get club name from clubs_df and apply shorthand
        club_name = clubs_df[clubs_df['club_id'] == club_id]['name'].iloc[0] if not clubs_df[
            clubs_df['club_id'] == club_id].empty else "Unknown"
        club_name_shorthand = get_club_shorthand(club_name)

        # Append to results
        results.append({
            'club_id': club_id,
            'club_name': club_name_shorthand,
            'total_value': total_value,
            'club_size': club_size,
            **position_values  # Add position-wise values as separate columns
        })

    # Convert results to a DataFrame
    club_stats_df = pd.DataFrame(results)

    club_stats_df = club_stats_df.merge(ranking_df[['club_id', 'Rank']], on='club_id', how='left')

    # Sort clubs by rank
    club_stats_df.sort_values(by='Rank', inplace=True)

    melted = club_stats_df.melt(
        id_vars=['club_name', 'club_id'],  # Include 'club_id' here
        value_vars=position_values.keys(),
        var_name='Position',
        value_name='Value'
    )

    # add market value formating as a column
    club_stats_df['formatted_total_value'] = club_stats_df['total_value'].apply(format_market_value)
    melted['formatted_value'] = melted['Value'].apply(format_market_value)


    # Adjust figure based on dropdown selection
    if scope_value == "all":
        # Create a stacked bar chart for position values
        fig = px.bar(
            melted,
            x='club_name',
            y='Value',
            color='Position',
            title='Club Market Value by Position',
            labels={'club_name': 'Club', 'Value': 'Market Value (EUR)'},
            color_discrete_map=position_color_map,
            custom_data=['club_id' ,'club_name', 'Position', 'formatted_value'],
        )
        # Update hover template
        fig.update_traces(
            hovertemplate=(
                "<b>%{customdata[1]}</b><br>"
               # "<b>Position:</b> %{customdata[2]}<br>"
                "Market Value: %{customdata[3]}<br>"
                "<extra></extra>"
            )
        )

    else:
        # Create a bar chart for the selected position

        # Filter the data for the selected position
        filtered_data = melted[melted['Position'] == scope_value]
        # Create a bar chart for the selected position
        fig = px.bar(
            filtered_data,
            x='club_name',
            y='Value',
            title=f'Club Market Value for {scope_value}',
            labels={'club_name': 'Club', 'Value': 'Market Value (EUR)'},
            custom_data=['club_id', 'club_name', 'formatted_value']
        )

        # Update hover template
        fig.update_traces(
            hovertemplate=(
                "<b>%{customdata[1]}</b><br>"
                "Market Value:> %{customdata[2]}<br>"
                "<extra></extra>"
            )
        )
        fig.update_traces(marker_color=position_color_map[scope_value])
    fig.update_layout(
        legend=dict(
            orientation="v",  # Vertical orientation
            yanchor="top",    # Align to the top
            y=1,              # Position it at the top
            xanchor="right",  # Align to the right
            x=1               # Position it on the right
        )
    )
    # Add total value as text above bars (optional for stacked bar chart)
    if scope_value == "all":
        for i, club_name in enumerate(club_stats_df['club_name']):
            total_value = club_stats_df.loc[club_stats_df['club_name'] == club_name, 'total_value'].values[0]
            fig.add_annotation(
                x=club_name,
                y=total_value,
                text=f"{total_value / 1e6:.2f}M",
                showarrow=False,
                font=dict(size=10),
                align="center",
                xanchor="center",
                yanchor="bottom"
            )

    return fig, club_stats_df.to_dict('records')


@callback(
    Output("team-dropdown", "value", allow_duplicate=True),
    Input("clubs-value-graph", "clickData"),
    prevent_initial_call=True
)
def display_selected_club(clickData):
    if clickData is None or 'points' not in clickData:
        return None

    # Extract the club_id from customdata
    point = clickData['points'][0]  # The first point clicked
    club_id = point['customdata'][0]  # The first element in customdata (club_id)

    return club_id
