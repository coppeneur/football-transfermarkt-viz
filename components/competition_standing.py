from dash import html, dcc, Input, Output, callback, dash_table
import dash_bootstrap_components as dbc
from utils.consts import *
import plotly.express as px
from utils.utilsFunctions import get_club_shorthand

competition_standing_component = dbc.Card(
    dbc.CardBody([
        dcc.Store(id="rankings-data-store"),
        dash_table.DataTable(
            id='rankings-table',
            columns=[
                {'name': 'Rank', 'id': 'Rank'},
                {'name': 'Team', 'id': 'Team'},
                {'name': 'Wins', 'id': 'Wins'},
                {'name': 'Losses', 'id': 'Losses'},
                {'name': 'Draws', 'id': 'Draws'},
                {'name': 'GF', 'id': 'GF'},
                {'name': 'GA', 'id': 'GA'},
                {'name': 'GD', 'id': 'GD'},
                {'name': 'Points', 'id': 'Points'}
            ],
            style_table={'overflowX': 'auto'},
            page_size=20
        ),
        # html.Div(id='selected-club-id', style={'margin-top': '10px'})
    ]),
    className="m-2"
)


def calculate_ranking(data):
    # Create an empty dictionary to store team stats
    teams_stats = {}

    for _, row in data.iterrows():
        # Home team stats
        home_team = get_club_shorthand(row['home_club_name'])
        away_team = get_club_shorthand(row['away_club_name'])
        home_goals = row['home_club_goals']
        away_goals = row['away_club_goals']
        home_team_id = row['home_club_id']
        away_team_id = row['away_club_id']

        if home_team not in teams_stats:
            teams_stats[home_team] = {'club_id': home_team_id, 'Wins': 0, 'Losses': 0, 'Draws': 0, 'GF': 0, 'GA': 0,
                                      'Points': 0}
        if away_team not in teams_stats:
            teams_stats[away_team] = {'club_id': away_team_id, 'Wins': 0, 'Losses': 0, 'Draws': 0, 'GF': 0, 'GA': 0,
                                      'Points': 0}

        # Update goals for and against
        teams_stats[home_team]['GF'] += home_goals
        teams_stats[home_team]['GA'] += away_goals
        teams_stats[away_team]['GF'] += away_goals
        teams_stats[away_team]['GA'] += home_goals

        # Update wins, losses, draws, and points
        if home_goals > away_goals:
            teams_stats[home_team]['Wins'] += 1
            teams_stats[home_team]['Points'] += 3
            teams_stats[away_team]['Losses'] += 1
        elif home_goals < away_goals:
            teams_stats[away_team]['Wins'] += 1
            teams_stats[away_team]['Points'] += 3
            teams_stats[home_team]['Losses'] += 1
        else:
            teams_stats[home_team]['Draws'] += 1
            teams_stats[away_team]['Draws'] += 1
            teams_stats[home_team]['Points'] += 1
            teams_stats[away_team]['Points'] += 1

    # Convert stats dictionary to a DataFrame
    ranking_df = pd.DataFrame.from_dict(teams_stats, orient='index')
    ranking_df.index.name = 'Team'
    ranking_df.reset_index(inplace=True)
    ranking_df['GD'] = ranking_df['GF'] - ranking_df['GA']
    ranking_df.sort_values(by=['Points', 'GD', 'GF'], ascending=[False, False, False], inplace=True)
    ranking_df.reset_index(drop=True, inplace=True)

    # Add Rank column
    ranking_df['Rank'] = ranking_df.index + 1
    return ranking_df


@callback([Output("rankings-table", "data"),
           Output("rankings-data-store", "data")],
          [Input("competition-dropdown", "value"),
           Input("season-competition-dropdown", "value")]
          )
def update_rankings(selected_competition_id, selected_season):
    if selected_competition_id is None or selected_season is None:
        return [], None

    filtered_games = games_df[
        (games_df["competition_id"] == selected_competition_id) & (games_df["season"] == selected_season)]

    rankings = calculate_ranking(filtered_games)

    return rankings.to_dict('records'), rankings.to_dict('records')


# @callback(
#     Output("selected-club-id", "children"),
#     [Input("rankings-table", "active_cell"),
#      Input("rankings-table", "data")]
# )
# def display_selected_club(active_cell, table_data):
#     if active_cell is None:
#         return "No club selected."
#
#     row_index = active_cell['row']
#     if row_index < len(table_data):
#         club_id = table_data[row_index].get('club_id', "123")
#         return f"Selected Club ID: {club_id}"
#     return "Invalid selection."


@callback(
    Output("team-dropdown", "value"),
    [Input("rankings-table", "active_cell"),
     Input("rankings-table", "data")]
)
def change_team_dropdown(active_cell, table_data):
    if active_cell is None:
        return None

    row_index = active_cell['row']
    if row_index < len(table_data):
        club_id = table_data[row_index].get('club_id', "123")
        return club_id
    return None
