from dash import html, dcc, Input, Output, callback
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from utils.consts import *
from utils.utilsFunctions import get_club_shorthand
from utils.tol_colors import tol_cset

# Card containing the figure
win_loss_component = dbc.Card(
    dbc.CardBody([
        dcc.Dropdown(
            id="win-loss-scope-dropdown",
            options=[
                {"label": "Complete", "value": "complete"},
                {"label": "Home", "value": "home"},
                {"label": "Away", "value": "away"},
            ],
            value="complete",
        ),
        dcc.Graph(id="win-loss-clubs-graph")
    ]),
    className="m-2"
)

# Get high-contrast colors from Paul Tol's palette
high_contrast_colors = tol_cset('high-contrast')

color_discrete_map = {
    "win": high_contrast_colors.blue,    # Blue for wins
    "loss": high_contrast_colors.red,    # Red for losses
    "draw": high_contrast_colors.yellow  # Yellow for draws
}


@callback(
    Output("win-loss-clubs-graph", "figure"),
    [
        Input("competition-dropdown", "value"),
        Input("season-competition-dropdown", "value"),
        Input("win-loss-scope-dropdown", "value"),
        Input("rankings-data-store", "data")
    ]
)
def update_win_loss_figure(selected_competition_id, selected_season, scope, rankings_data):
    if selected_competition_id is None or selected_season is None or rankings_data is None:
        return {}

    # Convert rankings data back to DataFrame
    ranking_df = pd.DataFrame(rankings_data)

    filtered_games = games_df[
        (games_df["competition_id"] == selected_competition_id) & (games_df["season"] == selected_season)
        ]

    # Initialize results list
    results = []

    for _, row in filtered_games.iterrows():
        home_id = row['home_club_id']
        away_id = row['away_club_id']
        home_goals = row['home_club_goals']
        away_goals = row['away_club_goals']

        if scope in ["complete", "home"]:
            if home_goals > away_goals:
                results.append({'club_id': home_id, 'win': 1, 'loss': 0, 'draw': 0})
            elif home_goals < away_goals:
                results.append({'club_id': home_id, 'win': 0, 'loss': 1, 'draw': 0})
            else:
                results.append({'club_id': home_id, 'win': 0, 'loss': 0, 'draw': 1})

        if scope in ["complete", "away"]:
            if away_goals > home_goals:
                results.append({'club_id': away_id, 'win': 1, 'loss': 0, 'draw': 0})
            elif away_goals < home_goals:
                results.append({'club_id': away_id, 'win': 0, 'loss': 1, 'draw': 0})
            else:
                results.append({'club_id': away_id, 'win': 0, 'loss': 0, 'draw': 1})

    # Create a DataFrame from results and summarize
    results_df = pd.DataFrame(results)
    summary = results_df.groupby('club_id').sum().reset_index()
    title_map = {
        "complete": "Complete: Wins, Draws, and Losses by Club (Percentage)",
        "home": "Home: Wins, Draws, and Losses by Club (Percentage)",
        "away": "Away: Wins, Draws, and Losses by Club (Percentage)"
    }

    # Calculate total games played and percentage for each result
    summary['total_games'] = summary[['win', 'loss', 'draw']].sum(axis=1)
    summary['win_percentage'] = (summary['win'] / summary['total_games']) * 100
    summary['loss_percentage'] = (summary['loss'] / summary['total_games']) * 100
    summary['draw_percentage'] = (summary['draw'] / summary['total_games']) * 100

    # Merge with club information and sort by points
    summary = summary.merge(ranking_df[['club_id', 'Rank']], on='club_id', how='left')
    summary = summary.merge(clubs_df, left_on='club_id', right_on='club_id')
    summary['name'] = summary['name'].apply(get_club_shorthand)
    summary.sort_values(by='Rank', inplace=True, ascending=False)

    # Add columns for the number of games for each result type
    summary['win_games'] = summary['win']
    summary['draw_games'] = summary['draw']
    summary['loss_games'] = summary['loss']

    # Melt data for plotting
    melted = summary.melt(
        id_vars=['club_id', 'name', 'total_games', 'win_games', 'draw_games', 'loss_games'],
        value_vars=['win_percentage', 'draw_percentage', 'loss_percentage'],
        var_name='Result',
        value_name='Percentage'
    )

    # Set the correct order for the "Result" column
    result_order = ['win_percentage', 'draw_percentage', 'loss_percentage']
    melted['Result'] = melted['Result'].astype(pd.CategoricalDtype(categories=result_order, ordered=True))

    # Rename "Result" values for better display in the chart
    result_display_map = {
        'win_percentage': 'win',
        'draw_percentage': 'draw',
        'loss_percentage': 'loss'
    }
    melted['Result'] = melted['Result'].map(result_display_map)

    # Add a column for dynamic display of "x out of y games"
    melted['games_count'] = melted.apply(
        lambda row: row['win_games'] if row['Result'] == 'win' else (
            row['draw_games'] if row['Result'] == 'draw' else row['loss_games']
        ),
        axis=1
    )

    # Generate the figure
    fig = px.bar(
        melted,
        x='Percentage',
        y='name',
        color='Result',
        orientation='h',
        barmode='stack',
        labels={"name": "Club", "Percentage": "Percentage (%)"},
        title=title_map[scope],
        color_discrete_map=color_discrete_map,
        custom_data=['name', 'Result', 'Percentage', 'total_games', 'games_count']
    )

    # Update hovertemplate for better labeling
    fig.update_traces(
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"  # Club name
            "%{customdata[1]}: %{customdata[4]} out of %{customdata[3]} games<br>"  # Result and game count
            "Percentage: %{customdata[2]:.1f}%<extra></extra>"  # Percentage
        )
    )

    # Update layout
    fig.update_layout(
        xaxis_title="Percentage of Games (%)",
        yaxis_title="Club",
        legend_title="Result",
        xaxis_tickformat=".1f",  # Format x-axis as percentage
        margin=dict(t=50, l=120, r=50, b=50)
    )

    return fig
