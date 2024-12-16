from dash import dcc, html, Input, Output, callback
import plotly.express as px
import pandas as pd
from utils.utilsFunctions import load_team_games_data, get_club_shorthand
from utils.consts import RESULT_COLORS
import logging
import plotly.graph_objects as go
from utils.tol_colors import tol_cset  # cset for the categoricals cmap for continuous

logging.basicConfig(level=logging.INFO)

game_lineups_df = pd.read_csv('data/game_lineups.csv')

team_games_success_component = html.Div([
    html.Div([
        dcc.Graph(id='team-games-scatterplot', className="scatterplot"),
        html.Div(id='selected-game-output', className="game-details")
    ], className="scatterplot-details-container")
])


@callback(
    Output('team-games-scatterplot', 'figure'),
    [
        Input("team-dropdown", "value"),
        Input("season-competition-dropdown", "value"),
        Input("competition-dropdown", "value")
    ]
)
def update_team_games_scatterplot(team_id, selected_season, competition):
    team_games_df = load_team_games_data(team_id=team_id)
    team_games_df = team_games_df.sort_values('date')

    # Filter games based on selected season range
    if team_games_df['season'].dtype.name == 'category':
        team_games_df['season'] = team_games_df['season'].astype(int)
    team_games_df = team_games_df[
        (team_games_df['season'] == selected_season)
    ]

    if competition:
        team_games_df = team_games_df[team_games_df['competition_id'] == competition]

    # Check if the game has a lineup - this variable we use later on to make the marker transparent
    team_games_df['has_lineup'] = team_games_df['game_id'].isin(game_lineups_df['game_id'])

    # Home/Away mapping
    team_games_df['game_type'] = team_games_df['home_away'].map({'Home': 'H', 'Away': 'A'})

    team_games_df['opponent_row'] = team_games_df['season'].astype(str) + " - " + team_games_df['opponent']

    team_games_df['game_index'] = team_games_df['game_type']
    team_games_df['team_id'] = team_id

    team_games_df = team_games_df.sort_values(['season', 'opponent'])

    # Compute opponent index
    team_games_df['opponent_index'] = team_games_df.groupby(['season', 'opponent']).ngroup()

    # Increase spacing factor to reduce clutter
    spacing_factor = 100
    team_games_df['Opponents'] = team_games_df['opponent_index'] * spacing_factor

    team_games_df['Game Type'] = team_games_df['game_type']

    # Importing the high-contrast colors by Paul Tol
    high_contrast_colors = tol_cset('high-contrast')

    team_games_df['marker_color'] = team_games_df['result'].map({
        'win': high_contrast_colors.blue,
        'draw': high_contrast_colors.yellow,
        'loss': high_contrast_colors.red
    })

    team_games_df['opponent'] = team_games_df['opponent'].apply(get_club_shorthand)

    fig = go.Figure()

    for result, color in zip(['win', 'draw', 'loss'],
                             [high_contrast_colors.blue,
                              high_contrast_colors.yellow,
                              high_contrast_colors.red]):
        result_df = team_games_df[team_games_df['result'] == result]
        fig.add_trace(go.Scatter(
            x=result_df['Game Type'],
            y=result_df['Opponents'],
            mode='markers',
            marker=dict(
                symbol='square',
                size=15,
                line=dict(width=0),
                color=color,
                opacity=result_df['has_lineup'].map({True: 1.0, False: 0.3}).tolist()  # Apply opacity to data points
            ),
            name=result.capitalize(),  # Single legend entry for each result type
            legendgroup=result.capitalize(),  # Group by result type
            showlegend=True,  # Ensure this trace appears in the legend
            customdata=result_df[[
                'game_id', 'opponent', 'home_club_goals', 'away_club_goals', 'date',
                'team_id', 'opponent_id', 'playing_team_name', 'home_away', 'has_lineup'
            ]].values,
            hovertemplate=(
                "<b>%{customdata[1]}</b><br>"
                "Date: %{customdata[4]}<br>"
                "Result: %{customdata[2]} - %{customdata[3]}<br>"
                "Lineup Available: %{customdata[9]}<br>"
                "<extra></extra>"
            )
        ))

        # Ensure full opacity for legend markers
        fig.add_trace(go.Scatter(
            x=[None],  # No data points
            y=[None],
            mode='markers',
            marker=dict(
                symbol='square',
                size=15,
                line=dict(width=0),
                color=color,
                opacity=1.0  # Full opacity for the legend marker
            ),
            name=result.capitalize(),
            legendgroup=result.capitalize(),  # Same group to link with data trace
            showlegend=False  # Hide dummy trace from the legend
        ))

    # Update layout for legend and axes
    fig.update_layout(
        title="Team Game Results by Opponent",
        xaxis=dict(
            title="Game Type",
            type='category',
            ticktext=['Home', 'Away'],
            tickvals=['H', 'A'],
            tickmode='array',
            range=[-0.5, 1.5],
            zeroline=False
        ),
        yaxis=dict(
            title="Opponents",
            tickvals=team_games_df['opponent_index'] * spacing_factor,
            ticktext=team_games_df['opponent'],
            tickmode='array'
        ),
        legend=dict(
            title="Game Result",
            orientation="v",
            x=1.05,
            y=0.5,
            xanchor="left",
            yanchor="middle"
        ),
        width=600,
        height=600,
        margin=dict(l=0, r=0, t=50, b=0)
    )

    return fig


@callback(
    Output('selected-game-output', 'children'),
    Input('team-games-scatterplot', 'clickData')
)
def handle_game_click(click_data):
    if click_data and 'customdata' in click_data['points'][0]:
        game_id = click_data['points'][0]['customdata'][0]
        opponent_name = click_data['points'][0]['customdata'][1]
        home_goals = click_data['points'][0]['customdata'][2]
        away_goals = click_data['points'][0]['customdata'][3]
        date = click_data['points'][0]['customdata'][4]
        team_id = click_data['points'][0]['customdata'][5]
        opponent_id = click_data['points'][0]['customdata'][6]
        playing_team_name = click_data['points'][0]['customdata'][7]
        home_away = click_data['points'][0]['customdata'][8]

        # Split date into Day, Month, Year
        date_parts = date.split("-")
        year = date_parts[0]
        month = date_parts[1]
        day = date_parts[2]

        home_logo = get_team_logo(team_id if home_away == 'Home' else opponent_id)
        away_logo = get_team_logo(opponent_id if home_away == 'Home' else team_id)

        playing_team_name = get_club_shorthand(playing_team_name)

        game_details = html.Div([
            html.Div([
                html.H4("Selected Game Details:", className="game-details-header"),
                html.Div([
                    # Top section: Our Date container
                    html.Div([
                        html.Div([
                            html.P("Day", className="date-label-day"),
                            html.P(day, className="date-value-day")
                        ], className="date-segment-day"),
                        html.Div([
                            html.P("Month", className="date-label-month"),
                            html.P(month, className="date-value-month")
                        ], className="date-segment-month"),
                        html.Div([
                            html.P("Year", className="date-label-year"),
                            html.P(year, className="date-value-year")
                        ], className="date-segment-year"),
                    ], className="date-container"),

                    # Middle Section: Club Names, Home/Away Labels
                    html.Div([
                        html.Div([
                            html.P(playing_team_name if home_away == 'Home' else opponent_name,
                                   className="club-name-home"),
                            html.P("Home", className="home-label")
                        ], className="club-segment-home"),
                        html.Div([
                            html.P(opponent_name if home_away == 'Home' else playing_team_name,
                                   className="club-name-away"),
                            html.P("Away", className="away-label")
                        ], className="club-segment-away"),
                    ], className="club-names-container"),

                    # Lower Section: Club Logos and Score
                    html.Div([
                        html.Img(src=home_logo, className="club-logo-home"),
                        html.Div([
                            html.P(home_goals, className="score-home"),
                            html.P(":", className="score-separator"),
                            html.P(away_goals, className="score-away"),
                        ], className="score-container"),
                        html.Img(src=away_logo, className="club-logo-away"),
                    ], className="score-and-logos-container"),

                ], className="details-row"),
            ], className="game-details-card")
        ])
        return game_details

    return "No game selected."


def get_team_logo(club_id):
    """
    Returns the logo URL for a given club ID, logic pretty similar to the dropdown
    """
    if club_id:
        return f"https://tmssl.akamaized.net//images/wappen/head/{club_id}.png"
    return "/assets/no-image-svgrepo-com.svg"
