import pandas as pd
import plotly.express as px
from utils.tol_colors import tol_cset
import os

# Set the correct root directory for your project
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # Adjust as needed
data_folder = os.path.join(base_dir, 'data')

# Define the paths to all CSV files
files = {
    "appearances": os.path.join(data_folder, 'appearances.csv'),
    "clubGames": os.path.join(data_folder, 'club_games.csv'),
    "clubs": os.path.join(data_folder, 'clubs.csv'),
    "competitions": os.path.join(data_folder, 'competitions.csv'),
    "gameEvents": os.path.join(data_folder, 'game_events.csv'),
    "gameLineups": os.path.join(data_folder, 'game_lineups.csv'),
    "games": os.path.join(data_folder, 'games.csv'),
    "player_valuations": os.path.join(data_folder, 'player_valuations.csv'),
    "players": os.path.join(data_folder, 'players.csv'),
    "transfers": os.path.join(data_folder, 'transfers.csv'),
    "seasons": os.path.join(data_folder, 'seasons.csv'),
}

# Load the DataFrames
try:
    appearances_df = pd.read_csv(files["appearances"])
    clubGames_df = pd.read_csv(files["clubGames"])
    clubs_df = pd.read_csv(files["clubs"])
    competitions_df = pd.read_csv(files["competitions"])
    gameEvents_df = pd.read_csv(files["gameEvents"])
    gameLineups_df = pd.read_csv(files["gameLineups"])
    games_df = pd.read_csv(files["games"])
    player_valuations_df = pd.read_csv(files["player_valuations"])
    players_df = pd.read_csv(files["players"])
    transfers_df = pd.read_csv(files["transfers"])
    seasons_df = pd.read_csv(files["seasons"])
    print("All files loaded successfully!")
except FileNotFoundError as e:
    print(f"Error loading file: {e}")
    print(f"Contents of 'data/' directory: {os.listdir(data_folder) if os.path.exists(data_folder) else 'Data folder not found'}")


# Get the bright colorscale from Paul Tol's palette, excluding yellow, blue, and red
vibrant_colors = [color for i, color in enumerate(tol_cset('vibrant')) if i not in [1, 4, 6]]  # Exclude blue, red (because we use them for win/loss) and gray (because we only need 4 colors)

# We use this map, so that in our position specific barcharts the bars will have the same color
position_color_map = {
    "Attack": vibrant_colors[0],
    "Midfield": vibrant_colors[1],
    "Defender": vibrant_colors[2], 
    "Goalkeeper": vibrant_colors[3]
}

RESULT_COLORS = {
    'win': 'green',
    'draw': 'yellow',
    'loss': 'red'
}

