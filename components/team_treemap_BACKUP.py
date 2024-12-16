from dash import dcc, Input, Output, callback
import dash_bootstrap_components as dbc
from utils.consts import *
from utils.utilsFunctions import *

team_playtime_marketvalue_component = dbc.Card(
    dbc.CardBody([
        dcc.Graph(id='team-playtime-marketvalue-scatter-chart')
    ]),
    className="m-2"
)


@callback(
    Output('team-playtime-marketvalue-scatter-chart', 'figure'),
    Input('team-dropdown', 'value'),
    Input('season-competition-dropdown', 'value'),
    Input('competition-dropdown', 'value'),
    Input('team-market-value-bar-chart', 'hoverData')
)
def update_playtime_marketvalue(selected_team, selected_season, selected_competition, hover_data):
    if selected_team is None:
        return {}

    # Filter games and appearances
    relevant_games = games_df[
        ((games_df['home_club_id'] == selected_team) | (games_df['away_club_id'] == selected_team)) &
        (games_df['season'] == selected_season) & (games_df['competition_id'] == selected_competition)
        ]
    relevant_game_ids = relevant_games['game_id'].unique()

    relevant_appearances = appearances_df[
        (appearances_df['game_id'].isin(relevant_game_ids)) &
        (appearances_df['player_club_id'] == selected_team)
        ]
    relevant_appearances['minutes_played'] = pd.to_numeric(
        relevant_appearances['minutes_played'], errors='coerce').fillna(0)

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

    # Add market value information
    evaluation = get_player_market_value_by_season(team_players, selected_season, selected_competition)
    evaluation = evaluation.rename(columns={'market_value_in_eur': 'current_market_value_in_eur'})
    team_players = team_players.merge(evaluation, on='player_id', how='left')
    team_players = team_players[team_players['current_market_value_in_eur'].notna()]

    team_players = team_players.merge(relevant_appearances, on='player_id', how='left')
    team_players['minutes_per_game'] = team_players['minutes_played'] / team_players['total_games']

    # Handle hover data for highlighting
    highlight_player_id = None
    if hover_data and 'points' in hover_data and hover_data['points']:
        highlight_player_id = hover_data['points'][0].get('customdata', None)

    # Handle hover data for highlighting
    highlight_player_id = None
    if hover_data and 'points' in hover_data and hover_data['points']:
        # Extract the single ID from hover_data['points'][0]['customdata']
        highlight_player_id = hover_data['points'][0].get('customdata', None)


    annotations = []
    if highlight_player_id:
        highlight_player_id = highlight_player_id[0] if isinstance(highlight_player_id, list) else highlight_player_id
        if highlight_player_id in team_players['player_id'].values:
            player_row = team_players[team_players['player_id'] == highlight_player_id]
            # get player_label
            player_label = generate_player_label(player_row)
            annotations.append(dict(
                x=player_row['minutes_played'].values[0],
                y=player_row['current_market_value_in_eur'].values[0],
                text="Player: " + player_label,
                showarrow=True,
                arrowhead=2,
                ax=0,
                ay=-40
            ))
    # Create the scatter plot
    fig = px.scatter(
        team_players,
        x='minutes_played',
        y='current_market_value_in_eur',
        size='total_games',
        color='position',
        hover_name='name',
        hover_data={
            'minutes_per_game': True,
            'current_market_value_in_eur': ':.2f',
            'total_games': True,
            'goals': True,
            'assists': True,
            'yellow_cards': True,
            'red_cards': True,
        },
        color_discrete_map=position_color_map
    )

    fig.update_layout(
        xaxis_title=f'Minutes Played in {selected_competition} ({selected_season})',
        yaxis_title='Market Value (EUR)',
        legend_title='Position',
    )
    fig.update_layout(annotations=annotations)

    return fig
