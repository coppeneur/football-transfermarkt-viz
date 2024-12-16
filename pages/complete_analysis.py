from dash import html
import dash_bootstrap_components as dbc
from components.competition_selector import competition_selector_component
from components.competition_standing import *
from components.competition_winloss import *
from components.competition_clubs_value import *
from components.team_playtime_marketvalue import *
from components.team_selector import *
from components.team_top_scorer import *
from components.team_treemap import *
from components.team_market_value_bar_chart import *
from components.competition_map import *
from components.player_lineup import *
from components.team_games_success import *
from components.player_selector import *
from components.player_marketvalue import *
from components.infobox import infobox_component

complete_analysis_page_content = dbc.Container([
    dbc.Row([
        dbc.Col(competition_selector_component, width=5),
        dbc.Col(infobox_component, width=7)
    ]),
    dbc.Row([
        dbc.Col(competition_standing_component, width=7),
        dbc.Col(competition_map_component, width=5)
    ]),
    dbc.Row([
        dbc.Col(win_loss_component, width=12)
    ]),
    dbc.Row([
        dbc.Col(clubs_value_component, width=12)
    ]),
    dbc.Row([
        dbc.Col(team_selector_component, width=5),
        dbc.Col(team_treemap, width=7)
    ]),
    dbc.Row([
        dbc.Col(team_market_value_bar_chart_component, width=12)
    ]),
    dbc.Row([
        dbc.Col(team_playtime_marketvalue_component, width=6),
        dbc.Col(team_top_scorers_component, width=6),
    ]),
    dbc.Row([
        dbc.Col(player_selector_component, width=4),
        dbc.Col(player_marketvalue_component, width=8),
    ]),
    dbc.Row([
        dbc.Col(team_games_success_component, width=12),
    ]),
    dbc.Row([
        dbc.Col(player_lineup_component, width=12),
    ]),
])
