from dash import dcc, Input, Output, callback, html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from utils.consts import *
from utils.utilsFunctions import *

team_playtime_marketvalue_component = dbc.Card(
    dbc.CardBody([
        dcc.Graph(id='team-playtime-marketvalue-scatter-chart'),
        html.Div(id="team-playtime-clickdata", className="mt-2", style={"font-weight": "bold"}),
    ]),
    className="m-2"
)


@callback(
    Output('clicked-player-store', 'data', allow_duplicate=True),
    Input('team-playtime-marketvalue-scatter-chart', 'clickData'),
    prevent_initial_call=True
)
def update_clicked_player(click_data):
    if click_data and 'points' in click_data and click_data['points']:
        player_id = click_data['points'][0]['customdata'][0]
        return player_id
    return None


@callback(
    Output('team-playtime-marketvalue-scatter-chart', 'figure'),
    Input('team-dropdown', 'value'),
    Input('season-competition-dropdown', 'value'),
    Input('competition-dropdown', 'value'),
    Input('treemap-store', 'data'),
    Input('clicked-player-store', 'data'),

)
def update_playtime_marketvalue(selected_team, selected_season, selected_competition, treemap_data, clicked_player_id):
    if selected_team is None:
        return {}

    relevant_games = games_df[
        ((games_df['home_club_id'] == selected_team) | (games_df['away_club_id'] == selected_team)) &
        (games_df['season'] == selected_season) & (games_df['competition_id'] == selected_competition)
        ]

    relevant_game_ids = relevant_games['game_id'].unique()

    relevant_appearances = appearances_df[
        (appearances_df['game_id'].isin(relevant_game_ids)) &
        (appearances_df['player_club_id'] == selected_team)
        ]

    relevant_appearances.loc[:, 'minutes_played'] = pd.to_numeric(relevant_appearances['minutes_played'],
                                                                  errors='coerce').fillna(0)

    relevant_appearances = relevant_appearances.groupby('player_id').agg(
        minutes_played=pd.NamedAgg(column='minutes_played', aggfunc='sum'),
        goals=pd.NamedAgg(column='goals', aggfunc='sum'),
        assists=pd.NamedAgg(column='assists', aggfunc='sum'),
        yellow_cards=pd.NamedAgg(column='yellow_cards', aggfunc='sum'),
        red_cards=pd.NamedAgg(column='red_cards', aggfunc='sum'),
        total_games=pd.NamedAgg(column='game_id', aggfunc='count')
    ).reset_index()

    relevant_player_ids = relevant_appearances['player_id'].unique()
    team_players = players_df[players_df['player_id'].isin(relevant_player_ids)]

    evaluation = get_player_market_value_by_season(team_players, selected_season, selected_competition)
    evaluation = evaluation.rename(columns={'market_value_in_eur': 'current_market_value_in_eur'})
    team_players = team_players.merge(evaluation, on='player_id', how='left')
    team_players = team_players[team_players['current_market_value_in_eur'].notna()]

    team_players = team_players.merge(relevant_appearances, on='player_id', how='left')

    path = treemap_data['path']
    if path:
        team_filter = path[0] if len(path) > 0 else None
        position_filter = path[1] if len(path) > 1 else None
        if position_filter in team_players['position'].unique():
            team_players = team_players[team_players['position'] == position_filter]

    team_players['minutes_per_game'] = team_players['minutes_played'] / team_players['total_games']

    # Handle clickData to highlight the selected player
    team_players['opacity'] = 1.0  # Default full opacity
    if clicked_player_id and clicked_player_id in team_players['player_id'].values:
        team_players.loc[team_players['player_id'] != clicked_player_id, 'opacity'] = 0.2
    else: # Reset opacity if no player is clicked
        team_players['opacity'] = 1

    # transform the market value to
    team_players['end_of_season_market_value'] = team_players['current_market_value_in_eur'].apply(format_market_value)
    fig = px.scatter(
        team_players,
        x='minutes_played',
        y='total_games',
        size='current_market_value_in_eur',
        color='position',
        hover_name='name',
        color_discrete_map=position_color_map,
        custom_data=[
            'player_id',
            'name',
            'minutes_played',
            'minutes_per_game',
            'end_of_season_market_value',
            'total_games',
            'yellow_cards',
            'red_cards',
        ],
    )
    fig.update_traces(
        hovertemplate=(
            "<b>%{customdata[1]}</b><br>"  # Player Name
            "Minutes Played: %{customdata[2]}<br>"  # Minutes Played
            "Games Played: %{customdata[5]}<br>"  # Games Played
            "Minutes/Game: %{customdata[3]:.1f}<br>"  # Minutes per Game
            "Market Value: %{customdata[4]}<br>"  # Market Value
            "Yellow Cards: %{customdata[6]}<br>"  # Yellow Cards
            "Red Cards: %{customdata[7]}"  # Red Cards
        )
    )

    # TODO Add a dummy dot size trace for the legend
#    fig.add_trace(
#        go.Scatter(
#            x=[None],  # No data points
#            y=[None],
#            mode="markers",
#            marker=dict(size=20, color="gray", opacity=0.5),  # Example size and color
#            showlegend=True,
#            name="Dot size = Market Value"  # Custom legend entry
#        )
#    )

    fig.update_layout(
        legend=dict(
            orientation="h",  # Horizontal orientation
            yanchor="top",  # Align legend to the bottom of its container
            y=-0.2,  # Position it slightly above the top of the chart
            xanchor="center",  # Center the legend horizontally
            x=0.5,  # Position the legend in the center
            font=dict(
                size=10  # Adjust the font size to make the legend smaller
            )
        )
    )

    # Add an opacity column to team_players
    team_players['opacity'] = 1
    if clicked_player_id and clicked_player_id in team_players['player_id'].unique():
        team_players['opacity'] = team_players['player_id'].apply(
            lambda player_id: 1 if player_id == clicked_player_id else 0.3
        )

    # Update marker opacity in each trace
    for trace in fig.data:
        trace_ids = team_players[team_players['position'] == trace.name]['player_id']
        trace_opacity = team_players.loc[team_players['player_id'].isin(trace_ids), 'opacity'].tolist()
        trace.marker.opacity = trace_opacity

    fig.update_layout(
        title=f"Minutes Played vs Games Played in {get_competition_name(selected_competition)} - {get_season_name(selected_season)}",
        xaxis_title="Minutes Played",
        yaxis_title="Games played",
        legend_title="Position"
    )

    # Add a dummy trace for bubble size legend
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker=dict(size=20, color="gray", opacity=0.5),
            showlegend=True,
            name="Bubble size increasing with market value"
        )
    )

    # Annotate bubbles with market value
    fig.update_traces(
        textposition='top center',
        textfont=dict(size=9, color='black')
    )

    return fig
