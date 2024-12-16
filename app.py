import dash
import os
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output
import pandas as pd
import zipfile


def extract_zip(zip_file_path_1, zip_file_path_2, extract_to_folder):
    if not os.path.exists(extract_to_folder):
        os.makedirs(extract_to_folder)
        with zipfile.ZipFile(zip_file_path_1, 'r') as zip_ref:
            zip_ref.extractall(extract_to_folder)
        with zipfile.ZipFile(zip_file_path_2, 'r') as zip_ref:
            zip_ref.extractall(extract_to_folder)
        print(f"Extracted '{zip_file_path_1}' and '{zip_file_path_2}' to '{extract_to_folder}'.")
    else:
        print(f"Folder '{extract_to_folder}' already exists. Skipping extraction.")


def create_seasons_df(games_df):
    first_game = games_df.groupby(['competition_id', 'season'])['date'].min().reset_index()

    # rename the date column to first_game
    seasons = first_game.rename(columns={'date': 'start'})
    last_game = games_df.groupby(['competition_id', 'season'])['date'].max().reset_index()
    seasons = seasons.merge(last_game, on=['competition_id', 'season'])

    # rename the date column to last_game
    seasons = seasons.rename(columns={'date': 'end'})
    # reorder the columns season should be the first column
    seasons = seasons[['season', 'competition_id', 'start', 'end']]
    # order by season
    seasons = seasons.sort_values(by='season')

    # get last two digits of season and add 1 to get the season name for example 20/21 for season 2020
    seasons['season_name'] = seasons['season'].apply(lambda x: f"{str(x)[2:]}/{str(x + 1)[2:]}")

    seasons.to_csv('data/seasons.csv', index=False)
    return seasons


zip_file_1 = 'data1.zip'
zip_file_2 = 'data2.zip'
data_folder = os.path.join('data', 'clubs.csv')

# TODO remove season.csv from gitrepo
if not os.path.exists(data_folder):
    extract_zip(zip_file_1, zip_file_2, 'data/')
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path_games = os.path.join(base_dir, 'data', 'games.csv')
    gamesdf = pd.read_csv(file_path_games)
    create_seasons_df(gamesdf)

from pages import complete_analysis  # Import pages

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
app.title = "FootballVis"

# Expose the server for Gunicorn
server = app.server

navbar = dbc.NavbarSimple(
    children=[
        dbc.ButtonGroup(
            [
                dbc.Button("Reset Selected Competition", id="reset-competition-button"),
                dbc.Button("Reset Selected Team", id="reset-team-button"),
                dbc.Button("Reset Selected Player", id="reset-player-button"),
            ],
            size="sm",  # Makes buttons smaller
        ),
    ],
    brand="FootballVis Dashboard",
    brand_href="/",
    color="primary",
    dark=True,
    sticky="top"
)

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),  # To manage routing
    navbar,
    html.Div(id="page-content", className="p-5"),  # Dynamic page content
])


@app.callback(
    Output("clicked-player-store", "data", allow_duplicate=True),
    [Input("reset-player-button", "n_clicks")],
    prevent_initial_call=True
)
def reset_player_store(n_clicks):
    if n_clicks:
        return None
    return dash.no_update


@app.callback(
    [Output("clicked-player-store", "data", allow_duplicate=True),
     Output("team-dropdown", "value", allow_duplicate=True)],
    [Input("reset-team-button", "n_clicks")],
    prevent_initial_call=True
)
def reset_store(n_clicks):
    if n_clicks:
        return None, None
    return dash.no_update


@app.callback(
    [Output("clicked-player-store", "data", allow_duplicate=True),
     Output("team-dropdown", "value", allow_duplicate=True),
     Output('season-competition-dropdown', 'value', allow_duplicate=True),
     Output('competition-dropdown', 'value', allow_duplicate=True),
     ],
    [Input("reset-competition-button", "n_clicks")],
    prevent_initial_call=True
)
def reset_store(n_clicks):
    if n_clicks:
        return None, None, None, None
    return dash.no_update


@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def routing(pathname):
    if pathname == "/":
        return complete_analysis.complete_analysis_page_content

    else:
        return dbc.Alert("404: Page not found", color="danger")


if __name__ == "__main__":
    app.run_server(debug=False)
