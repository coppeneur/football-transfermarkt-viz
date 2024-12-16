from dash import dcc, html, Input, Output, callback
import pandas as pd
import json
from utils.utilsFunctions import position_coordinates, calculate_player_gpa, interpolate_market_value, get_player_market_value_by_season
from datetime import datetime
import numpy as np
from utils.tol_colors import tol_cmap
from matplotlib.colors import Normalize

game_lineups_df = pd.read_csv('data/game_lineups.csv')
player_valuations_df = pd.read_csv('data/player_valuations.csv')
games_df = pd.read_csv('data/games.csv')
game_events_df = pd.read_csv('data/game_events.csv')

player_lineup_component = html.Div([
    dcc.Store(id='player-data-store'),
    dcc.Store(id='market-data-store'),
    dcc.Store(id='colormap-store'),
    html.Div(
        id="d3-visualization-container",
        className="d3-container",
        **{"data-player-data": json.dumps([]), "data-market-data": json.dumps([]), "data-colormap": json.dumps([])}
    )
])


def convert_to_native_types(data):
    """
    Recursively convert all pandas-specific data types in a list or dict
    to Python native data types (e.g., int64 -> int).
    """
    if isinstance(data, list):
        return [convert_to_native_types(item) for item in data]
    elif isinstance(data, dict):
        return {key: convert_to_native_types(value) for key, value in data.items()}
    elif isinstance(data, (pd.Timestamp, pd.Timedelta)):
        return str(data)
    elif isinstance(data, (np.integer, np.floating)):
        return data.item()
    return data

# Colormap and normalization (0 to 3), but we'll adjust dynamically
cmap = tol_cmap('BuRd')
norm = Normalize(vmin=0, vmax=3)

def generate_colormap_and_legend(gpa_values):
    # Compute min and max GPA
    min_gpa = min(gpa_values)
    max_gpa = max(gpa_values)

    colormap_steps = 256
    cmap_stops = []
    gray_color = "#cccccc"  # Gray color for ranges outside min-max

    # If min_gpa > 0, add gray from 0 to min_gpa
    if min_gpa > 0:
        cmap_stops.append({"value": 0, "color": gray_color})
        cmap_stops.append({"value": min_gpa, "color": gray_color})

    # Add the dynamic range for [min_gpa, max_gpa]
    for i in range(colormap_steps):
        val = min_gpa + (max_gpa - min_gpa) * (i / (colormap_steps - 1))
        norm_val = (val - min_gpa) / (max_gpa - min_gpa)  # normalized to [0,1]
        rgba = cmap(norm_val)
        hex_color = "#{:02x}{:02x}{:02x}".format(
            int(rgba[0] * 255), int(rgba[1] * 255), int(rgba[2] * 255)
        )
        cmap_stops.append({"value": val, "color": hex_color})

    # If max_gpa < 3, add gray from max_gpa to 3
    if max_gpa < 3:
        cmap_stops.append({"value": max_gpa, "color": gray_color})
        cmap_stops.append({"value": 3, "color": gray_color})

    legend = {
        "stops": cmap_stops,
        "min_gpa": 0,
        "max_gpa": 3,
        "dynamic_min": min_gpa,
        "dynamic_max": max_gpa,
    }

    return legend

@callback(
    [
        Output('player-data-store', 'data'),
        Output('market-data-store', 'data'),
        Output('colormap-store', 'data')
    ],
    [
        Input('team-games-scatterplot', 'clickData'),
        Input('team-dropdown', 'value')
    ]
)
def update_player_positions_with_offsets(click_data, team_id):
    if team_id is None:
        return json.dumps([]), json.dumps([]), json.dumps([])

    # If clickData exists, but the team_id in clickData doesn't match the dropdown, then someone must have changed their dropdown selection -> we should clear the chart
    if click_data and 'customdata' in click_data['points'][0]:
        team_id_from_click = click_data['points'][0]['customdata'][5]
        if team_id_from_click != team_id:
            return json.dumps([]), json.dumps([]), json.dumps([])
        
    try:
        #print(f"Received clickData: {click_data}")
        if click_data and 'customdata' in click_data['points'][0]:
            game_id = click_data['points'][0]['customdata'][0]
            team_id = click_data['points'][0]['customdata'][5]
            game_date = click_data['points'][0]['customdata'][4]

            print("Game ID:", game_id)

            players_in_game = game_lineups_df[
                (game_lineups_df["game_id"] == game_id) &
                (game_lineups_df["club_id"] == team_id) &
                (game_lineups_df["type"] == "starting_lineup")
            ]
            if players_in_game.empty:
                print("No lineup data for this game.")
                return json.dumps([]), json.dumps([]), json.dumps([])

            target_date = pd.to_datetime(game_date, errors='coerce')
            if target_date is pd.NaT:
                print("Invalid target_date.")
                return json.dumps([]), json.dumps([]), json.dumps([])

            # Filter game events for this game and team to include both "Goals" and "Cards"
            events_this_game = game_events_df[
                (game_events_df["game_id"] == game_id) & 
                (game_events_df["type"].isin(["Goals", "Cards"]))
            ]

            # Dictionaries to store cards and goals for each player
            player_cards = {}
            player_goals = {}

            for _, event_row in events_this_game.iterrows():
                p_id = event_row["player_id"]
                desc = str(event_row["description"]).lower()

                # Process cards
                card_list = player_cards.setdefault(p_id, [])
                if "red" in desc:
                    card_list.append("red")
                elif "yellow" in desc:
                    card_list.append("yellow")

                # Process goals - the upper one is too exclusive the lower one sometimes will count assists (especially own goal assists)
                #if event_row["type"] == "Goals" and ("header" in desc or "goal" in desc or "shot" in desc or "Goal" in desc or "Header" in desc or "Shot" in desc) and "assist" not in desc and "Assist" not in desc:
                if event_row["type"] == "Goals" and ("header" in desc or "goal" in desc or "shot" in desc or "Goal" in desc or "Header" in desc or "Shot" in desc):
                    goal_list = player_goals.setdefault(p_id, [])
                    goal_list.append("goal")


            position_groups = {}
            for _, player_row in players_in_game.iterrows():
                position = player_row.get("position")
                if position not in position_groups:
                    position_groups[position] = []
                position_groups[position].append(player_row)

            players_data = []
            market_values = []
            gpa_values = []

            season = target_date.year
            competition_id = games_df.loc[games_df["game_id"] == game_id, "competition_id"].iloc[0]

            # Get player market values for the specified season and competition
            player_market_values = get_player_market_value_by_season(players_in_game, season, competition_id)

            for position, players in position_groups.items():
                coords = position_coordinates.get(position, (0, 0))
                base_x, base_y = coords
                num_players = len(players)

                if num_players == 1:
                    player = players[0]
                    player_id = player.get("player_id", None)

                    # We have to extract the market value for this player, because our new utils function returns a df?
                    player_market_value = player_market_values.loc[
                        player_market_values["player_id"] == player_id, "market_value_in_eur"
                    ].iloc[0] if not player_market_values.empty else None

                    #print(player_market_value)

                    gpa = calculate_player_gpa(player_id, games_df, game_lineups_df)
                    gpa_values.append(gpa)
                    cards = player_cards.get(player_id, [])

                    players_data.append({
                        "name": player.get("player_name", "Unknown"),
                        "position": position,
                        "gpa": gpa,
                        "goals": player_goals.get(player_id, []),
                        "cards": cards,
                        "x": base_x,
                        "y": base_y
                    })
                    market_values.append({
                        "id": player_id,
                        "name": player.get("player_name", "Unknown"),
                        "market_value": player_market_value,
                        "gpa": gpa,
                        "position": position,
                        "x": base_x,
                        "y": base_y
                    })
                else:
                    offset_spacing = 2.5
                    start_offset = -(num_players - 1) / 2
                    for i, player in enumerate(players):
                        offset_x = base_x + (start_offset + i) * offset_spacing
                        player_id = player.get("player_id", None)

                        player_market_value = player_market_values.loc[
                        player_market_values["player_id"] == player_id, "market_value_in_eur"
                        ].iloc[0] if not player_market_values.empty else None

                        #print(player_market_value)
                        
                        gpa = calculate_player_gpa(player_id, games_df, game_lineups_df)
                        gpa_values.append(gpa)
                        cards = player_cards.get(player_id, [])

                        players_data.append({
                            "name": player.get("player_name", "Unknown"),
                            "position": position,
                            "gpa": gpa,
                            "goals": player_goals.get(player_id, []),
                            "cards": cards,
                            "x": offset_x,
                            "y": base_y
                        })
                        market_values.append({
                            "id": player_id,
                            "name": player.get("player_name", "Unknown"),
                            "market_value": player_market_value,
                            "gpa": gpa,
                            "position": position,
                            "x": offset_x,
                            "y": base_y
                        })
            #print("Players data:", players_data)
            if not gpa_values:
                # No GPAs found
                return json.dumps([]), json.dumps([]), json.dumps([])

            # Dynamically adjust colors now
            min_gpa, max_gpa = min(gpa_values), max(gpa_values)
            dynamic_norm = Normalize(vmin=min_gpa, vmax=max_gpa)

            # Re-assign colors based on dynamic range
            for player_data in players_data:
                gpa = player_data['gpa']
                normed_gpa = dynamic_norm(gpa)
                rgba = cmap(normed_gpa)
                hex_color = "#{:02x}{:02x}{:02x}".format(
                    int(rgba[0]*255), int(rgba[1]*255), int(rgba[2]*255)
                )
                player_data['color'] = hex_color

            for mv in market_values:
                gpa = mv['gpa']
                normed_gpa = dynamic_norm(gpa)
                rgba = cmap(normed_gpa)
                hex_color = "#{:02x}{:02x}{:02x}".format(
                    int(rgba[0]*255), int(rgba[1]*255), int(rgba[2]*255)
                )
                mv['color'] = hex_color

            legend = generate_colormap_and_legend(gpa_values)

            players_data = convert_to_native_types(players_data)
            market_values = convert_to_native_types(market_values)
            return players_data, market_values, legend

    except Exception as e:
        print(f"Error: {str(e)}")
        print(f"Full error details: {e.__class__.__name__}")

    return [], [], []


@callback(
    [
        Output('d3-visualization-container', 'data-player-data'),
        Output('d3-visualization-container', 'data-market-data'),
        Output('d3-visualization-container', 'data-colormap')
    ],
    [
        Input('player-data-store', 'data'),
        Input('market-data-store', 'data'),
        Input('colormap-store', 'data')
    ]
)
def sync_stores_to_attributes(player_data, market_data, colormap_data):
    #print("Debug - Colormap data:", colormap_data)
    return (
        json.dumps(player_data or []),
        json.dumps(market_data or []),
        json.dumps(colormap_data or {})
    )
