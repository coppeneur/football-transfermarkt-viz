from dash import html, dcc, Input, Output, callback
import dash_bootstrap_components as dbc
from utils.consts import *
from utils.utilsFunctions import *

all_team_options = [
    {"label": get_club_shorthand(row["name"]), "value": row["club_id"]} for _, row in clubs_df.iterrows()
]

all_competition_options = [
    {"label": get_competition_name(comp), "value": comp}
    for comp in clubs_df['domestic_competition_id'].unique()
    if pd.notnull(comp)
]

team_selector_component = dbc.Card(
    dbc.CardBody([
        dbc.Row([
            dbc.Col([
                html.Img(
                    id="team-image",
                    src="/assets/no-image-svgrepo-com.svg",
                    style={"width": "100%", "maxWidth": "150px"},
                    className="mx-auto d-block"
                )
            ]),
            dbc.Col([
                dcc.Dropdown(
                    id="team-dropdown",
                    options=all_team_options,
                    placeholder="Select a team",
                    style={"width": "100%", "whiteSpace": "nowrap"},
                    className="mb-2"
                )
            ]),
        ]),
    ]),
    className="m-2"
)


@callback(
    [Output("team-image", "src"),
     Output('treemap-store', 'data', allow_duplicate=True),
     ],
    Input("team-dropdown", "value"),
    prevent_initial_call=True
)
def update_team_info(selected_team_id):
    if selected_team_id is None:
        return "/assets/no-image-svgrepo-com.svg", {'path': [], 'player_id': None}

    image_src = f"https://tmssl.akamaized.net//images/wappen/head/{selected_team_id}.png"

    return image_src, {'path': [], 'player_id': None}


@callback(
    Output("team-dropdown", "options"),
    [
        Input("competition-dropdown", "value"),
        Input("season-competition-dropdown", "value")
    ]
)
def filter_teams_by_competition_and_season(selected_competition_id, selected_season):
    if selected_competition_id and selected_season:
        # We filter the games for the selected competition and season
        filtered_games = games_df[
            (games_df["competition_id"] == selected_competition_id) &
            (games_df["season"] == int(selected_season))
            ]
        # Based on the games we collect all team ids from the games in the competition & season
        team_ids = pd.concat([
            filtered_games["home_club_id"],
            filtered_games["away_club_id"]
        ]).unique()

        # Now that we have these ids, we collect them from the clubs_df (need this to get club names rather than ids)
        filtered_teams = clubs_df[clubs_df["club_id"].isin(team_ids)]

        # Generate dropdown options
        team_options_filtered = [
            {"label": get_club_shorthand(row["name"]), "value": row["club_id"]} for _, row in filtered_teams.iterrows()
        ]
        return team_options_filtered

    # If no competition or season is selected, return all teams
    return all_team_options
