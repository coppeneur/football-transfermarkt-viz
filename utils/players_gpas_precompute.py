import pandas as pd
import numpy as np
import os
import math

# Adjust these parameters as needed
CHUNK_SIZE = 5000  # Number of players to process before writing partial results and printing progress

# Load data once
print("Loading data...")
games_df = pd.read_csv('data/games.csv')
lineups_df = pd.read_csv('data/game_lineups.csv')

print("Merging data...")
# Merge datasets
merged_df = lineups_df.merge(
    games_df[["game_id", "home_club_id", "away_club_id", "home_club_goals", "away_club_goals"]],
    on="game_id",
    how="inner"
)

print("Calculating points vectorized...")
# Vectorized calculation of points
conditions = [
    (merged_df["club_id"] == merged_df["home_club_id"]) & (merged_df["home_club_goals"] > merged_df["away_club_goals"]),
    (merged_df["club_id"] == merged_df["home_club_id"]) & (merged_df["home_club_goals"] == merged_df["away_club_goals"]),
    (merged_df["club_id"] == merged_df["away_club_id"]) & (merged_df["away_club_goals"] > merged_df["home_club_goals"]),
    (merged_df["club_id"] == merged_df["away_club_id"]) & (merged_df["away_club_goals"] == merged_df["home_club_goals"])
]
choices = [3, 1, 3, 1]
merged_df["points"] = np.select(conditions, choices, default=0)

print("Extracting unique players...")
all_players = merged_df["player_id"].unique()
total_players = len(all_players)
print(f"Found {total_players} unique players.")

# Sort players to have a deterministic order (not strictly needed, but good for clarity)
all_players.sort()

# Prepare output paths
final_output_path = 'data/player_gpas.csv'
partial_output_path = 'data/player_gpas_partial.csv'

# If partial file exists from a previous run, optionally you can load it and skip processed players.
# For now, we always start fresh.
if os.path.exists(partial_output_path):
    os.remove(partial_output_path)

# We'll process players in chunks
num_chunks = math.ceil(total_players / CHUNK_SIZE)

print(f"Starting GPA computation in {num_chunks} chunks of up to {CHUNK_SIZE} players each...")

# We'll need a DataFrame to accumulate results if you want to write in chunks
# But writing directly in chunks might be more memory-friendly
# We'll just compute and write chunk by chunk
for i in range(num_chunks):
    start_idx = i * CHUNK_SIZE
    end_idx = min(start_idx + CHUNK_SIZE, total_players)
    player_subset = all_players[start_idx:end_idx]

    # Filter merged_df for these players
    subset_df = merged_df[merged_df["player_id"].isin(player_subset)]

    # Group by player_id and calculate mean points
    gpa_chunk = subset_df.groupby("player_id")["points"].mean().reset_index(name="gpa")

    # Append to partial file
    if i == 0:
        # Write header for the first time
        gpa_chunk.to_csv(partial_output_path, index=False, mode='w')
    else:
        # Append to existing file
        gpa_chunk.to_csv(partial_output_path, index=False, mode='a', header=False)

    print(f"Chunk {i+1}/{num_chunks} processed and saved. ({end_idx}/{total_players} players done)")

print("All chunks processed. Reading partial results to create final output...")
# Now read partial results and combine (if needed, they should already be combined)
final_gpa_df = pd.read_csv(partial_output_path)
# Ensure uniqueness if needed (there should be no duplicates if no interruptions)
final_gpa_df = final_gpa_df.drop_duplicates("player_id")

# Write final results
final_gpa_df.to_csv(final_output_path, index=False)
print(f"GPA calculations completed and saved to '{final_output_path}'.")
