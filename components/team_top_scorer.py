from dash import html, dcc, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

from utils.consts import *
from utils.utilsFunctions import *

team_top_scorers_component = dbc.Card(
    dbc.CardBody([
        dcc.Dropdown(
            id='scorer-chart-mode-dropdown',
            options=[
                {'label': 'Scorer Points', 'value': 'scorer_points'},
                {'label': 'Goals', 'value': 'goals'},
                {'label': 'Assists', 'value': 'assists'}
            ],
            value='scorer_points',
            clearable=False,
            style={'margin-bottom': '20px'}
        ),
        dcc.Graph(id='top-scorers-assists-graph'),
    ]),
    className="m-2"
)

# Merge appearances_df with games_df to include the season column
merged_df = appearances_df.merge(games_df[['game_id', 'season']], on='game_id', how='left')


@callback(
    Output('top-scorers-assists-graph', 'figure'),
    [
        Input('team-dropdown', 'value'),
        Input('season-competition-dropdown', 'value'),
        Input('competition-dropdown', 'value'),
        Input('scorer-chart-mode-dropdown', 'value'),
        Input('treemap-store', 'data'),
        Input('clicked-player-store', 'data')
    ]
)
def update_top_scorers_graph(selected_team, selected_season, selected_competition, chart_mode, treemap_data,
                             clicked_player_id):
    if not selected_team:
        return {}

    # Filter data for selected team, season, and competition
    relevant_games = games_df[
        ((games_df['home_club_id'] == selected_team) | (games_df['away_club_id'] == selected_team)) &
        (games_df['season'] == selected_season) & (games_df['competition_id'] == selected_competition)
        ]

    relevant_game_ids = relevant_games['game_id'].unique()

    relevant_appearances = appearances_df[
        (appearances_df['game_id'].isin(relevant_game_ids)) &
        (appearances_df['player_club_id'] == selected_team)
        ]

    # Aggregate goals and assists
    scorer_data = relevant_appearances.groupby('player_id').agg(
        goals=pd.NamedAgg(column='goals', aggfunc='sum'),
        assists=pd.NamedAgg(column='assists', aggfunc='sum'),
        minutes_played=pd.NamedAgg(column='minutes_played', aggfunc='sum')
    ).reset_index()

    # Calculate metrics
    scorer_data['scorer_points'] = scorer_data['goals'] + scorer_data['assists']
    scorer_data['avg_time_per_goal'] = scorer_data['minutes_played'] / scorer_data['goals']
    scorer_data['avg_time_per_assist'] = scorer_data['minutes_played'] / scorer_data['assists']
    scorer_data['avg_time_per_point'] = scorer_data['minutes_played'] / scorer_data['scorer_points']

    # Handle division by zero (e.g., no goals or assists)
    scorer_data.replace([float('inf'), float('nan')], 0, inplace=True)

    # Merge with player data
    scorer_data = scorer_data.merge(players_df, on='player_id', how='left')
    scorer_data['player_label'] = generate_player_label(scorer_data)

    # Sort data based on the selected chart mode
    if chart_mode == 'scorer_points':
        scorer_data = scorer_data[scorer_data['scorer_points'] > 0].sort_values(by='scorer_points', ascending=False)
    elif chart_mode == 'goals':
        scorer_data = scorer_data[scorer_data['goals'] > 0].sort_values(by='goals', ascending=False)
    elif chart_mode == 'assists':
        scorer_data = scorer_data[scorer_data['assists'] > 0].sort_values(by='assists', ascending=False)

    path = treemap_data['path']
    if path:
        team_filter = path[0] if len(path) > 0 else None
        position_filter = path[1] if len(path) > 1 else None
        if position_filter in scorer_data['position'].unique():
            scorer_data = scorer_data[scorer_data['position'] == position_filter]

    scorer_data['opacity'] = 1.0
    if clicked_player_id and clicked_player_id in scorer_data['player_id'].values:
        scorer_data.loc[scorer_data['player_id'] != clicked_player_id, 'opacity'] = 0.2
    else:
        scorer_data['opacity'] = 1
    fig = go.Figure()

    if chart_mode == 'scorer_points':
        # Scorer points as stacked bar chart
        for position in scorer_data['position'].unique():
            position_data = scorer_data[scorer_data['position'] == position]

            # Trace for Goals
            fig.add_trace(
                go.Bar(
                    x=position_data['player_label'],
                    y=position_data['goals'],
                    name=f"{position} - Goals",
                    marker=dict(
                        color=position_color_map[position],
                        opacity=position_data['opacity']
                    ),
                    customdata=position_data[['player_id', 'name', 'scorer_points', 'goals', 'avg_time_per_goal', 'avg_time_per_point']],
                    hovertemplate=(
                        "<b>%{customdata[1]}</b><br>"
                        "Scorer Points: <b>%{customdata[2]}</b><br>"
                        "Avg Time/Point: %{customdata[5]:.1f} min<br>"
                        "Goals: %{customdata[3]}<br>"
                        "Avg Time/Goal: %{customdata[4]:.1f} min"
                    ),
                )
            )

            # Trace for Assists
            fig.add_trace(
                go.Bar(
                    x=position_data['player_label'],
                    y=position_data['assists'],
                    name=f"{position} - Assists",
                    marker=dict(
                        color=position_color_map[position],
                        pattern=dict(shape="x"),
                        opacity=position_data['opacity']
                    ),
                    customdata=position_data[['player_id', 'name', 'scorer_points', 'assists', 'avg_time_per_assist', 'avg_time_per_point']],
                    hovertemplate=(
                        "<b>%{customdata[1]}</b><br>"
                        "Scorer Points: <b>%{customdata[2]}</b><br>"
                        "Avg Time/Point: %{customdata[5]:.1f} min<br>"
                        "Assists: %{customdata[3]}<br>"
                        "Avg Time/Assist: %{customdata[4]:.1f} min"
                    ),
                )
            )

        # Stack bars
        fig.update_layout(barmode='stack')

    elif chart_mode == 'goals':
        # Only goals
        for position in scorer_data['position'].unique():
            position_data = scorer_data[scorer_data['position'] == position]

            fig.add_trace(
                go.Bar(
                    x=position_data['player_label'],
                    y=position_data['goals'],
                    name=f"{position} - Goals",
                    marker=dict(
                        color=position_color_map[position],
                        opacity=position_data['opacity']
                    ),
                    customdata=position_data[['player_id', 'name', 'goals', 'avg_time_per_goal']],
                    hovertemplate=(
                        "<b>%{customdata[1]}</b><br>"
                        "Goals: <b>%{customdata[2]}</b><br>"
                        "Avg Time/Goal: %{customdata[3]:.1f} min"
                    ),
                ),
            )

    elif chart_mode == 'assists':
        # Only assists
        for position in scorer_data['position'].unique():
            position_data = scorer_data[scorer_data['position'] == position]

            fig.add_trace(
                go.Bar(
                    x=position_data['player_label'],
                    y=position_data['assists'],
                    name=f"{position} - Assists",
                    marker=dict(
                        color=position_color_map[position],
                        pattern=dict(shape="x"),
                        opacity=position_data['opacity']
                    ),
                    customdata=position_data[['player_id', 'name', 'assists', 'avg_time_per_assist']],
                    hovertemplate=(
                        "<b>%{customdata[1]}</b><br>"
                        "Assists: <b>%{customdata[2]}</b><br>"
                        "Avg Time/Assist: %{customdata[3]:.1f} min"
                    ),
                )
            )

    # Update layout
    fig.update_layout(
        title=f'Top Scorers and Assists - Season {get_season_name(selected_season)}',
        xaxis_title='Players',
        yaxis_title='Goals and Assists' if chart_mode == 'scorer_points' else (
            'Goals' if chart_mode == 'goals' else 'Assists'),
        legend_title='Position and Metric',
        xaxis=dict(categoryorder='array', categoryarray=scorer_data['player_label'])  # Preserve sorting
    )

    return fig


@callback(
    Output('clicked-player-store', 'data', allow_duplicate=True),
    Input('top-scorers-assists-graph', 'clickData'),
    prevent_initial_call=True
)
def update_clicked_player(click_data):
    if click_data and 'points' in click_data and click_data['points']:
        player_id = click_data['points'][0]['customdata'][0]
        return player_id
    return None
