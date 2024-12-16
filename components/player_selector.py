from dash import html, dcc, Input, Output, callback
import dash_bootstrap_components as dbc
from utils.consts import *
from datetime import datetime

# Assuming players_df is already loaded
all_player_options = [
    {"label": row["name"], "value": row["player_id"]} for _, row in players_df.iterrows()
]


def calculate_age(birth_date):
    birth_date = datetime.strptime(birth_date.split(" ")[0], "%Y-%m-%d")
    today = datetime.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


player_selector_component = dbc.Card(
    dbc.CardBody([
        dbc.Row([
            dbc.Col([
                dcc.Dropdown(
                    id="player-dropdown",
                    options=all_player_options,
                    placeholder="Select a player",
                    style={"width": "100%", "whiteSpace": "nowrap"},
                    className="mb-2"
                ),
                html.Img(
                    id="player-image",
                    src="/assets/no-image-svgrepo-com.svg",
                    style={"width": "100%", "maxWidth": "150px"},
                    className="mx-auto d-block"
                ),
                html.Div(
                    id="player-details",
                    style={"textAlign": "center", "marginTop": "10px"},
                )
            ])
        ]),
    ]),
    className="m-2"
)


@callback(
    [
        Output("player-image", "src"),
        Output("player-details", "children")
    ],
    [Input("player-dropdown", "value")]
)
def update_player_details(player_id):
    if player_id:
        player = players_df[players_df["player_id"] == player_id].iloc[0]
        image_url = player["image_url"]
        age = calculate_age(player["date_of_birth"])
        details = []

        if age:
            details.append(html.P([html.B("Age:"), f" {age} years"], className="mb-1"))
        if player['height_in_cm']:
            details.append(html.P([html.B("Height:"), f" {player['height_in_cm']} cm"], className="mb-1"))
        if player['country_of_birth']:
            details.append(html.P([html.B("Country of Birth:"), f" {player['country_of_birth']}"], className="mb-1"))
        if player['foot']:
            details.append(html.P([html.B("Preferred Foot:"), f" {player['foot']}"], className="mb-1"))
        return image_url, html.Div(details)

    return "/assets/no-image-svgrepo-com.svg", html.P("No player selected.", className="text-muted")


@callback(
    Output("player-dropdown", "options"),
    [
        Input("team-dropdown", "value"),
        Input("competition-dropdown", "value"),
        Input("season-competition-dropdown", "value")
    ]
)
def filter_players_by_team(selected_team_id, selected_competition_id, selected_season):
    if selected_team_id and selected_competition_id and selected_season:
        relevant_games = games_df[
            ((games_df['home_club_id'] == selected_team_id) | (games_df['away_club_id'] == selected_team_id)) &
            (games_df['season'] == selected_season) &
            (games_df['competition_id'] == selected_competition_id)
            ]

        relevant_game_ids = relevant_games['game_id'].unique()
        relevant_appearances = appearances_df[
            (appearances_df['game_id'].isin(relevant_game_ids)) &
            (appearances_df['player_club_id'] == selected_team_id)
            ]
        relevant_player_ids = relevant_appearances['player_id'].unique()
        filtered_players = players_df[players_df['player_id'].isin(relevant_player_ids)]
        player_options = [
            {"label": row["name"], "value": row["player_id"]} for _, row in filtered_players.iterrows()
        ]
        return player_options

    return all_player_options


@callback(
    Output("player-dropdown", "value"),
    Input('clicked-player-store', 'data')
)
def update_player_dropdown(clicked_player_id):
    if clicked_player_id:
        return clicked_player_id
    return None
