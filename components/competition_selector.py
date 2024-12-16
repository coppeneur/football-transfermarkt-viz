from dash import html, dcc, Input, Output, callback
import dash_bootstrap_components as dbc
from utils.consts import *
from utils.utilsFunctions import *

all_competition_options = [
    {"label": get_competition_name(row["competition_id"]), "value": row["competition_id"]} for index, row in competitions_df.iterrows() if
    row["type"] == "domestic_league"
]
all_competition_options.sort(key=lambda x: x["label"])

competition_selector_component = dbc.Card(
    dbc.CardBody([
        dbc.Row([
            dbc.Col([
                html.Img(
                    id="competition-image",
                    src="/assets/no-image-svgrepo-com.svg",
                    style={"width": "100%", "maxWidth": "150px"},
                    className="mx-auto d-block"
                )
            ]),
            dbc.Col([
                dcc.Dropdown(
                    id="competition-dropdown",
                    options=all_competition_options,
                    placeholder="Select a league",
                    style={"width": "100%"},
                    className="mb-2"
                ),
                dcc.Dropdown(
                    id="season-competition-dropdown",
                    placeholder="Select a Season",
                    style={"width": "100%"},
                    className="mb-2"
                ),
            ])
        ])
    ]),
    className="m-2"
)


@callback([
    Output('competition-image', 'src'),
    Output('season-competition-dropdown', 'options'),
    Output('season-competition-dropdown', 'value')],
    [Input("competition-dropdown", "value"),
     Input("season-competition-dropdown", "value")]
)
def update_competition_info(selected_competition_id, current_season_value):
    if selected_competition_id is None:
        return "/assets/no-image-svgrepo-com.svg", [], None

    selected_competition_id_string = str(selected_competition_id)
    image_src = f"https://tmssl.akamaized.net//images/logo/header/{selected_competition_id_string.lower()}.png"

    filtered_games = games_df[games_df["competition_id"] == selected_competition_id]
    unique_seasons = filtered_games["season"].unique()

    season_mapping = dict(zip(seasons_df["season"], seasons_df["season_name"]))
    season_options = [{"label": season_mapping[season], "value": season} for season in unique_seasons if season in season_mapping]
    season_options.sort(key=lambda x: x["value"], reverse=True)

    if current_season_value in [option["value"] for option in season_options]:
        return image_src, season_options, current_season_value
    else:
        return image_src, season_options, None
