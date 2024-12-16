from dash import dcc, Input, Output, State, callback, html
import dash_bootstrap_components as dbc
import plotly.express as px
from utils.consts import *
from utils.utilsFunctions import *

# Include a Store for tracking path state
treemap_store = dcc.Store(id="treemap-store", data={'path': [], 'player_id': None})

team_treemap = dbc.Card(
    dbc.CardBody([
        dcc.Graph(id="team-market-value-treemap"),
        treemap_store
    ]),
    className="m-2"
)


@callback(
    Output('team-market-value-treemap', 'figure'),
    Input('team-dropdown', 'value'),
    Input('season-competition-dropdown', 'value'),
    Input('competition-dropdown', 'value'),
)
def update_team_treemap_chart(selected_team, selected_season, selected_competition):
    if selected_team is None:
        return {}

    # Filter `games_df` for the selected team and season
    relevant_games = games_df[
        ((games_df['home_club_id'] == selected_team) | (games_df['away_club_id'] == selected_team)) &
        (games_df['season'] == selected_season) &
        (games_df['competition_id'] == selected_competition)
        ]

    # Extract game IDs for the filtered games
    relevant_game_ids = relevant_games['game_id'].unique()

    # Use `appearances_df` to find players who appeared in these games for the selected team
    relevant_appearances = appearances_df[
        (appearances_df['game_id'].isin(relevant_game_ids)) &
        (appearances_df['player_club_id'] == selected_team)
        ]

    relevant_player_ids = relevant_appearances['player_id'].unique()

    team_players = players_df[players_df['player_id'].isin(relevant_player_ids)]

    evaluation = get_player_market_value_by_season(team_players, selected_season, selected_competition)
    evaluation = evaluation.rename(columns={'market_value_in_eur': 'current_market_value_in_eur'})
    team_players = team_players.merge(evaluation, on='player_id', how='left')
    team_players = team_players[team_players['current_market_value_in_eur'].notna()]
    team_players['player_label'] = generate_player_label(team_players)

    # Calculate market value percentages
    team_total_value = team_players['current_market_value_in_eur'].sum()
    team_players['position_total_value'] = team_players.groupby('position')['current_market_value_in_eur'].transform(
        'sum')
    team_players['market_value_percentage_position'] = (team_players['current_market_value_in_eur'] / team_players[
        'position_total_value']) * 100
    team_players['market_value_percentage_team'] = (team_players[
                                                        'current_market_value_in_eur'] / team_total_value) * 100
    team_players['formatted_market_value'] = team_players['current_market_value_in_eur'].apply(format_market_value)

    # Add a root layer for the team
    team_players["root"] = "Team"  # Adding a generic root node for the entire team

    team_root_color = "#FFFFFF"  # White for team root
    default_color = "#D3D3D3"  # Fallback color for unexpected levels

    fig = px.treemap(
        team_players,
        path=["root", "position", "player_label"],  # Define hierarchy
        values="current_market_value_in_eur",
        title="Market Value by Position",
        custom_data=["current_market_value_in_eur", "position_total_value"],
    )

    # Update all colors manually
    new_colors = []
    for sector in fig.data[0]["ids"]:
        # If the sector is the root node
        if sector == "Team":
            new_colors.append(team_root_color)
        # If it's a position node, map the position color
        elif len(sector.split("/")) > 1 and sector.split("/")[1] in position_color_map:
            position = sector.split("/")[1]
            new_colors.append(position_color_map.get(position, default_color))
        else:
            # Fallback color for unexpected cases
            new_colors.append(default_color)

    # Assign the updated colors to the figure
    fig.data[0]["marker"]["colors"] = new_colors

    fig.update_traces(
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Market Value: €%{value:,.0f}<br>"
            "% of Parent: %{percentParent:.1%}<br>"
            "% of Total: %{percentEntry:.1%}"
        )
    )

    # Update layout
    fig.update_layout(
        title=dict(x=0.5),
        margin=dict(t=50, l=25, r=25, b=25),
    )

    return fig


@callback(
    Output('treemap-store', 'data'),
    Input('team-market-value-treemap', 'clickData'),
    State('treemap-store', 'data')
)
def update_treemap_path(click_data, treemap_data):
    current_path = treemap_data['path']

    if click_data is None:
        # No click: Return current path
        return treemap_data

    # Extract the clicked path from clickData
    clicked_path = click_data['points'][0]['id'].split('/')

    if current_path and current_path == clicked_path:
        # If clicking the same item again, go back (remove the last segment of the path)
        current_path = current_path[:-1]
        if current_path:
            # Update position and player_id when going back
            last_segment = current_path[-1]
            last_click_data = next(
                (point for point in click_data['points'] if point['id'].endswith(last_segment)), None
            )
            if last_click_data and len(current_path) > 1:  # Ensure we're not on the top layer
                treemap_data['player_id'] = last_click_data['customdata'][1]
            else:
                treemap_data['player_id'] = None
        else:
            treemap_data['player_id'] = None
    else:
        # Otherwise, navigate forward
        current_path = clicked_path
        if len(current_path) > 1:  # Only set player_id if we're below the top layer
            treemap_data['player_id'] = click_data['points'][0]['customdata'][1]
        else:
            treemap_data['player_id'] = None

    # Update the path in the store
    treemap_data['path'] = current_path

    return treemap_data
