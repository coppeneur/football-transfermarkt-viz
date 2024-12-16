from dash import html, dcc, Input, Output, callback
import dash_bootstrap_components as dbc
from utils.consts import *
from utils.utilsFunctions import *

infobox_component = dbc.Card(
    dbc.CardBody([
        html.Div([
            html.P(
                "Begin by selecting a season and competition. This "
                "interactive dashboard provides intuitive and dynamic visualizations, enabling detailed analysis of "
                "team performance,"
                "player contributions, and market dynamics. Use this to uncover trends, compare metrics, "
                "and gain deeper insights into football data.",
                className="mb-0",
                style={
                    "fontSize": "14px",
                    "lineHeight": "1.6"
                }
            ),
            html.Br(),
            html.P(
                "This project was developed as part of the Data "
                "Visualization course, 2024, at Aarhus University.",
                className="mb-0",
                style={
                    "fontSize": "11px",
                    "lineHeight": "1.4"
                }
            )
        ])
    ]),
    className="m-2",
)
