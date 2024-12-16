from dash import dcc, Input, Output, callback, html
import dash_bootstrap_components as dbc
from utils.consts import *
from utils.utilsFunctions import *
from utils.tol_colors import tol_cset
import plotly.graph_objects as go

team_market_value_bar_chart_component = dbc.Card(
    dbc.CardBody([
        dcc.Graph(id="team-market-value-bar-chart"),
        dcc.Store(id='clicked-player-store', data=None),
    ]),
    className="m-2"
)


@callback(
    Output('team-market-value-bar-chart', 'figure'),
    [
        Input('team-dropdown', 'value'),
        Input("season-competition-dropdown", "value"),
        Input('competition-dropdown', 'value'),
        Input('treemap-store', 'data'),
        Input('clicked-player-store', 'data')
    ]
)
def update_market_value_bar_chart(selected_team, selected_season, selected_competition, treemap_data, clicked_player_id):
    if selected_team is None:
        return {}

    # Filter games for the selected team and season
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

    # Get unique player IDs for the filtered appearances
    relevant_player_ids = relevant_appearances['player_id'].unique()

    # Filter `players_df` for these player IDs
    team_players = players_df[players_df['player_id'].isin(relevant_player_ids)]

    evaluation = get_player_market_value_by_season(team_players, selected_season, selected_competition)
    evaluation = evaluation.rename(columns={'market_value_in_eur': 'current_market_value_in_eur'})
    team_players = team_players.merge(evaluation, on='player_id', how='left')
    team_players = team_players[team_players['current_market_value_in_eur'].notna()]
    team_players['player_label'] = generate_player_label(team_players)

    # Filter based on the treemap path (if applicable)
    path = treemap_data['path']
    if path:
        team_filter = path[0] if len(path) > 0 else None
        position_filter = path[1] if len(path) > 1 else None
        if position_filter in team_players['position'].unique():
            team_players = team_players[team_players['position'] == position_filter]

    # Sort players by market value in descending order (ignoring position groups)
    team_players = team_players.sort_values(by='current_market_value_in_eur', ascending=False)

    # Handle opacity for highlighting
    team_players['opacity'] = 1.0  # Default full opacity
    if clicked_player_id and clicked_player_id in team_players['player_id'].values:
        team_players.loc[team_players['player_id'] != clicked_player_id, 'opacity'] = 0.2
    else:  # Reset opacity if no player is clicked
        team_players['opacity'] = 1

    # Create bar chart with go.Figure
    fig = go.Figure()

    # Add a single trace with sorted data and color coding by position
    fig.add_trace(
        go.Bar(
            x=team_players['player_label'],  # Sorted labels
            y=team_players['current_market_value_in_eur'],  # Sorted values
            marker=dict(
                color=team_players['position'].map(position_color_map),  # Colors based on position
                opacity=team_players['opacity']  # Opacity for clicked highlight
            ),
            customdata=team_players['player_id'],  # Player IDs for interactivity
            hovertemplate="<b>%{x}</b><br>Market Value: €%{y}<extra></extra>"
        )
    )

    # Update layout
    fig.update_layout(
        barmode='stack',  # Use 'stack' for a single grouped view
        title=f'Market Value of Players - Season {get_season_name(selected_season)}',
        xaxis=dict(tickangle=-45, title='Players'),
        yaxis=dict(title='Market Value (in EUR)'),
        legend=dict(
            orientation="v",  # Vertical legend
            yanchor="top",
            y=1,  # Top position
            xanchor="right",
            x=1  # Right position
        ),
        title_x=0.5,
    )

    return fig

@callback(
    Output('clicked-player-store', 'data'),
    Input('team-market-value-bar-chart', 'clickData')
)
def display_click_data(click_data):
    if click_data is None or 'points' not in click_data or not click_data['points']:
        return None
    player_id = click_data['points'][0]['customdata']
    return player_id
