import zipfile
import os
import pandas as pd
from utils.consts import *

player_valuations_df = pd.read_csv('data/player_valuations.csv')





def get_competition_name(competition_id):
    competition_mapping = {
        'L1': 'Bundesliga',
        'RU1': 'Russian Premier League',
        'TR1': 'Turkish Super Lig',
        'IT1': 'Serie A',
        'GB1': 'Premier League',
        'BE1': 'Pro League',
        'DK1': 'Danish Superliga',
        'NL1': 'Eredivisie',
        'GR1': 'Super League Greece',
        'PO1': 'Primeira Liga',
        'SC1': 'Scottish Premiership',
        'ES1': 'La Liga',
        'UKR1': 'Ukrainian Premier League',
        'FR1': 'Ligue 1'
    }
    return competition_mapping.get(competition_id, competition_id)


position_coordinates = {
    "Goalkeeper": (0, 5),
    "Centre-Back": (0, 4),
    "Left-Back": (-3, 3),
    "Right-Back": (3, 3),
    "Defensive Midfield": (0, 2),
    "Central Midfield": (0, -1),
    "Left Midfield": (-3, 0),
    "Right Midfield": (3, 0),
    "Attacking Midfield": (0, -2),
    "Left Winger": (-4, -3),
    "Right Winger": (4, -3),
    "Centre-Forward": (0, -4),
    "Second Striker": (0, -3),
    "Sweeper": (0, 3),
    "Attack": (0, -5),
    "Defender": (0, 4),
    "midfield": (0, 0),
}


# TODO integrate this function into the app.py file as preprocessing step
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


# add utils functions to get the season name from the season id
def get_season_name(season_id):
    return seasons_df[seasons_df['season'] == season_id]['season_name'].values[0]


def get_player_market_value_by_season(player_df, season, competition_id):
    """
    Retrieve the market value of players during a specific season.

    Args:
        player_df (pd.DataFrame): DataFrame of players with at least 'player_id'.
        season (int): The season year.
        competition_id (str): The competition ID.
    Returns:
        pd.DataFrame: DataFrame with players and their market value for the specified season.
    """

    # Ensure dates are in datetime format
    seasons_df['start'] = pd.to_datetime(seasons_df['start'])
    seasons_df['end'] = pd.to_datetime(seasons_df['end'])
    player_valuations_df['date'] = pd.to_datetime(player_valuations_df['date'])

    # Get the season's start and end dates for the given competition
    season_info = seasons_df[(seasons_df['season'] == season) & (seasons_df['competition_id'] == competition_id)]

    if season_info.empty:
        raise ValueError(f"Season {season} with competition ID {competition_id} not found in seasons_df.")

    # Extract start and end dates
    start_date = season_info.iloc[0]['start']
    end_date = season_info.iloc[0]['end']

    if season == 2024:
        start_date = \
            seasons_df[(seasons_df['season'] == 2023) & (seasons_df['competition_id'] == competition_id)].iloc[0][
                'start']

    # Check for next season and update the end date if the next season is available
    next_season_info = seasons_df[
        (seasons_df['season'] == season + 1) & (seasons_df['competition_id'] == competition_id)]
    if not next_season_info.empty:
        end_date = next_season_info.iloc[0]['start']

    # Filter player evaluations for the given timeframe
    filtered_evaluations = player_valuations_df[
        (player_valuations_df['date'] >= start_date) &
        (player_valuations_df['date'] < end_date)
        ]
    # filter player evaluations to only contain the players from the player_df
    filtered_evaluations = filtered_evaluations[filtered_evaluations['player_id'].isin(player_df['player_id'])]
    # get only the latest market value of each player
    filtered_evaluations = filtered_evaluations.sort_values(by=['player_id', 'date']).groupby(
        'player_id').last().reset_index()

    # Merge player data with filtered evaluations
    player_values = player_df[['player_id']].merge(filtered_evaluations, on='player_id', how='left')

    if player_values.empty:
        raise ValueError(
            f"No matching player evaluations found. Inputs: season={season}, competition={competition_id}, players={len(player_df)}")

    # Sort and get the latest market value for each player
    latest_market_values = (
        player_values.sort_values(by=['player_id', 'date'])
        .groupby('player_id', as_index=False)
        .last()
    )

    # Return the relevant columns
    result = latest_market_values[['player_id', 'market_value_in_eur', 'date']]
    return result


def get_games_by_competition_and_season(games_df, competition_id, season):
    """
    Retrieve games for a specific competition and season.

    Args:
        games_df (pd.DataFrame): DataFrame of games with at least 'competition_id', 'season', 'home_club_id', and 'away_club_id'.
        competition_id (str): The competition ID.
        season (int): The season year.
    Returns:
        pd.DataFrame: DataFrame with games for the specified competition and season.
    """

    return games_df[(games_df['competition_id'] == competition_id) & (games_df['season'] == season)]


def get_clubs_from_games(selected_games_df):
    """
    Retrieve all unique clubs from the games DataFrame.

    Args:
        selected_games_df (pd.DataFrame): DataFrame of games with at least 'home_club_id' and 'away_club_id'.
    Returns:
        pd.Series: Series of unique club IDs.
    """
    home_club_ids = selected_games_df["home_club_id"]
    away_club_ids = selected_games_df["away_club_id"]
    club_ids = pd.concat([home_club_ids, away_club_ids]).unique()
    return clubs_df[clubs_df['club_id'].isin(club_ids)]


def interpolate_market_value(player_id, target_date):
    target_date = pd.to_datetime(target_date)

    # Filter the DataFrame for the specific player
    player_valuations = player_valuations_df[player_valuations_df["player_id"] == player_id].copy()

    if player_valuations.empty:
        return 0

    player_valuations["date"] = pd.to_datetime(player_valuations["date"])

    player_valuations = player_valuations.sort_values("date")

    # interpolation logic
    if target_date < player_valuations["date"].min():
        # If the target date is before the earliest valuation, return the first available value
        return player_valuations.iloc[0]["market_value_in_eur"]

    if target_date > player_valuations["date"].max():
        # If the target date is after the latest valuation, we return the last available value
        return player_valuations.iloc[-1]["market_value_in_eur"]

    before = player_valuations[player_valuations["date"] <= target_date].iloc[-1]
    after = player_valuations[player_valuations["date"] > target_date].iloc[0] if \
        not player_valuations[player_valuations["date"] > target_date].empty else before

    if before["date"] == after["date"]:
        return before["market_value_in_eur"]  # If both dates are the same, return the market value directly

    # Linear interpolation with the exact date
    interpolated_value = (
            before["market_value_in_eur"] +
            (after["market_value_in_eur"] - before["market_value_in_eur"]) *
            (target_date - before["date"]).days / (after["date"] - before["date"]).days
    )

    return round(interpolated_value, 2)


def load_team_games_data(team_id, season=None, competition_type=None, home_away=None):
    """
    Load and preprocess games data for a specific team.

    Args:
        team_id (int): The ID of the team to filter games for.
        season (str, optional): The season to filter games (e.g., '2020/2021'). Default is None.
        competition_type (str, optional): The type of competition to filter (e.g., 'League', 'Cup'). Default is None.
        home_away (str, optional): Filter for 'Home' or 'Away' games. Default is None.

    Returns:
        pd.DataFrame: Processed and filtered DataFrame ready for visualization.
    """
    games_df = pd.read_csv('data/games.csv')
    competitions_df = pd.read_csv('data/competitions.csv')

    # Filter games for the selected team
    team_games_df = games_df[
        (games_df['home_club_id'] == team_id) | (games_df['away_club_id'] == team_id)
        ].copy()

    # Determine game result for the selected team
    def determine_result(row):
        if (row['home_club_id'] == team_id and row['home_club_goals'] > row['away_club_goals']) or \
                (row['away_club_id'] == team_id and row['away_club_goals'] > row['home_club_goals']):
            return 'win'
        elif row['home_club_goals'] == row['away_club_goals']:
            return 'draw'
        else:
            return 'loss'

    team_games_df['result'] = team_games_df.apply(determine_result, axis=1)

    # Determine Home/Away status
    team_games_df['home_away'] = team_games_df.apply(
        lambda row: 'Home' if row['home_club_id'] == team_id else 'Away', axis=1
    )

    # Add Opponent ID and Name
    team_games_df['opponent_id'] = team_games_df.apply(
        lambda row: row['away_club_id'] if row['home_away'] == 'Home' else row['home_club_id'], axis=1
    )
    team_games_df['opponent'] = team_games_df.apply(
        lambda row: row['away_club_name'] if row['home_away'] == 'Home' else row['home_club_name'], axis=1
    )

    # Add Playing Team Name
    team_games_df['playing_team_name'] = team_games_df.apply(
        lambda row: row['home_club_name'] if row['home_away'] == 'Home' else row['away_club_name'], axis=1
    )

    team_games_df['result'] = team_games_df.apply(determine_result, axis=1)

    # Merge competition type information
    team_games_df = team_games_df.merge(
        competitions_df[['competition_id', 'type']],
        on='competition_id',
        how='left'
    )

    # Apply user filters (season, competition type, home/away)
    if season:
        team_games_df = team_games_df[team_games_df['season'] == season]

    if competition_type:
        team_games_df = team_games_df[team_games_df['type'] == competition_type]

    if home_away:
        team_games_df = team_games_df[team_games_df['home_away'] == home_away]

    # Prepare data for visualization
    # Ensure 'season' is categorical and ordered
    team_games_df['season'] = pd.Categorical(team_games_df['season'], ordered=True)

    # Custom hover data for visualization
    team_games_df['hover_data'] = team_games_df.apply(lambda row: {
        'date': row['date'],
        'opponent': row['opponent'],
        'score': f"{row['home_club_goals']} - {row['away_club_goals']}",
        'competition': row['type'],
        'location': row['home_away']
    }, axis=1)

    return team_games_df


def generate_player_label(team_players):
    """
    Generate player labels with the first letter of the first name and the full last name.
    If the first name is not present, use only the last name.
    If both are not present, use the 'name' column.

    Args:
        team_players (pd.DataFrame): DataFrame containing player information.

    Returns:
        pd.Series: Series of player labels.
    """
    return team_players.apply(
        lambda row: f"{row['first_name'][0]}. {row['last_name']}" if pd.notna(row['first_name']) and pd.notna(
            row['last_name']) else (row['last_name'] if pd.notna(row['last_name']) else row['name']),
        axis=1
    )


def calculate_player_gpa(player_id, games_df, game_lineups_df):
    """
    Calculate the Game Point Average (GPA) for a specific player based on all games they participated in.
    """
    # games_df = pd.read_csv('data/games.csv')
    # game_lineups_df = pd.read_csv('data/game_lineups.csv')

    # Get all games the player participated in
    player_games = game_lineups_df[game_lineups_df["player_id"] == player_id]

    # Merge with games_df to get game results
    merged = player_games.merge(
        games_df[["game_id", "home_club_id", "away_club_id", "home_club_goals", "away_club_goals"]],
        on="game_id",
        how="inner"
    )

    # Determine the result for each game
    def determine_game_points(row):
        if row["club_id"] == row["home_club_id"]:  # Player's team was the home team
            if row["home_club_goals"] > row["away_club_goals"]:
                return 3  # Win
            elif row["home_club_goals"] == row["away_club_goals"]:
                return 1  # Draw
            else:
                return 0  # Loss
        elif row["club_id"] == row["away_club_id"]:  # Player's team was the away team
            if row["away_club_goals"] > row["home_club_goals"]:
                return 3  # Win
            elif row["away_club_goals"] == row["home_club_goals"]:
                return 1  # Draw
            else:
                return 0  # Loss
        return 0  # No points if something goes wrong - not optimal because it could change the average - possible ToDo

    # Calculate points for each game
    merged["points"] = merged.apply(determine_game_points, axis=1)

    # Calculate GPA
    if not merged.empty:
        return merged["points"].mean()
    return 0.0  # Return 0 if the player has no games


def format_market_value(value):
    if pd.isna(value):  # Check for NaN
        return "N/A"
    if value >= 1_000_000:
        return f"€{value / 1_000_000:.1f}M"
    elif value >= 1_000:
        return f"€{value / 1_000:.1f}K"
    else:
        return f"€{value:.0f}"


def get_club_shorthand(full_name):
    """
    Returns the shorthand for a club name, or the original name if no shorthand is defined.
    """
    club_name_to_shorthand = ({
        "SV Darmstadt 98": "Darmstadt",
        "Ural Yekaterinburg": "Ural",
        "Beşiktaş Jimnastik Kulübü": "Beşiktaş",
        "Associazione Sportiva Roma": "AS Roma",
        "Tottenham Hotspur Football Club": "Tottenham Hotspur",
        "Koninklijke Atletiek Associatie Gent": "KAA Gent",
        "Hvidovre IF": "Hvidovre",
        "Football Club København": "FC København",
        "Roda JC Kerkrade": "Roda JC",
        "Yeni Malatyaspor": "Yeni Malatyaspor",
        "Veria NPS": "Veria",
        "AO Platanias": "Platanias",
        "AC Horsens": "Horsens",
        "B SAD": "B SAD",
        "Saint Johnstone Football Club": "St Johnstone",
        "Kieler Sportvereinigung Holstein von 1900": "Holstein Kiel",
        "Oud-Heverlee Leuven": "OH Leuven",
        "SK Beveren": "SK Beveren",
        "Académica Coimbra": "Académica",
        "Royal Standard Club de Liège": "Standard Liège",
        "SKA Khabarovsk": "SKA Khabarovsk",
        "FC Ingolstadt 04": "Ingolstadt",
        "Dundee Football Club": "Dundee FC",
        "SD Huesca": "Huesca",
        "Cardiff City": "Cardiff",
        "SC Dnipro-1": "Dnipro-1",
        "Goverla Uzhgorod (- 2016)": "Goverla",
        "Futebol Clube de Arouca": "FC Arouca",
        "MKE Ankaragücü": "Ankaragücü",
        "Hibernian Football Club": "Hibernian",
        "Montpellier Hérault Sport Club": "Montpellier",
        "Association Football Club Bournemouth": "Bournemouth",
        "Córdoba CF": "Córdoba",
        "Bologna Football Club 1909": "Bologna",
        "Lille Olympique Sporting Club Lille Métropole": "Lille",
        "Nîmes Olympique": "Nîmes",
        "Giresunspor": "Giresunspor",
        "Rangers Football Club": "Rangers",
        "Grupo Desportivo Estoril Praia": "Estoril",
        "Karpaty Lviv (-2021)": "Karpaty Lviv",
        "Kilmarnock Football Club": "Kilmarnock",
        "APO Levadiakos Football Club": "Levadiakos",
        "Vorskla Poltava": "Vorskla",
        "Hull City": "Hull",
        "Liverpool Football Club": "Liverpool",
        "Sporting Clube de Portugal": "Sporting",
        "Stade brestois 29": "Brest",
        "1.FC Nuremberg": "1.FC Nuremberg",
        "Udinese Calcio": "Udinese",
        "FC Sochi": "Sochi",
        "Amkar Perm": "Amkar",
        "Trabzonspor Kulübü": "Trabzonspor",
        "AE Larisa": "Larisa",
        "Metalist 1925 Kharkiv": "Metalist 1925",
        "Beerschot AC": "Beerschot",
        "SC Bastia": "Bastia",
        "İstanbul Başakşehir Futbol Kulübü": "Başakşehir",
        "Panthrakikos Komotini": "Panthrakikos",
        "Metalist Kharkiv": "Metalist Kharkiv",
        "Футбольный клуб \"Локомотив\" Москва": "Lokomotiv Moscow",
        "Watford FC": "Watford",
        "Deportivo Alavés S.A.D.": "Alavés",
        "FK Fakel Voronezh": "Fakel",
        "FC Lorient": "Lorient",
        "Silkeborg Idrætsforening": "Silkeborg",
        "Club Atlético de Madrid S.A.D.": "Atlético Madrid",
        "Futbol Club Barcelona": "Barcelona",
        "SC Cambuur Leeuwarden": "Cambuur",
        "Galatasaray Spor Kulübü": "Galatasaray",
        "RAEC Mons (- 2015)": "RAEC Mons",
        "Panionios Athens": "Panionios",
        "Borussia Verein für Leibesübungen 1900 Mönchengladbach": "Borussia Mönchengladbach",
        "PFK Lviv": "Lviv",
        "1. Fußballclub Heidenheim 1846": "Heidenheim",
        "Stade Rennais Football Club": "Rennes",
        "GD Chaves": "Chaves",
        "FC Penafiel": "Penafiel",
        "Real Valladolid Club de Fútbol S.A.D.": "Valladolid",
        "Sporting Clube Farense": "Farense",
        "Bodrumspor Spor Faaliyetleri Anonim Şirketi": "Bodrumspor",
        "Palermo FC": "Palermo",
        "Football Club Internazionale Milano S.p.A.": "Inter",
        "GS Ergotelis": "Ergotelis",
        "Niki Volou": "Niki Volou",
        "Sønderjyske Fodbold": "Sønderjyske",
        "Aris Thessalonikis": "Aris",
        "Football Club de Nantes": "Nantes",
        "Leicester City Football Club": "Leicester",
        "Calcio Como": "Como",
        "Brighton and Hove Albion Football Club": "Brighton",
        "SC Beira-Mar": "Beira-Mar",
        "FC Dordrecht": "Dordrecht",
        "FC Orenburg": "Orenburg",
        "Dundee United Football Club": "Dundee United",
        "Desna Chernigiv": "Desna",
        "Odense Boldklub": "Odense",
        "Football Club Utrecht": "Utrecht",
        "Brøndby Idrætsforening": "Brøndby",
        "RFC Seraing": "Seraing",
        "AEL Kalloni": "Kalloni",
        "Dijon FCO": "Dijon",
        "FC Paços de Ferreira": "Paços Ferreira",
        "Esbjerg fB": "Esbjerg",
        "Spezia Calcio": "Spezia",
        "Rotor Volgograd": "Rotor",
        "FK Obolon Kyiv": "Obolon",
        "Erzurumspor FK": "Erzurumspor",
        "FC Girondins Bordeaux": "Bordeaux",
        "Koninklijke Beerschot Voetbalclub Antwerpen": "Beerschot Antwerpen",
        "Heart of Midlothian Football Club": "Hearts",
        "Iraklis Thessaloniki": "Iraklis",
        "SC Olhanense": "Olhanense",
        "Antalyaspor": "Antalyaspor",
        "Adanaspor": "Adanaspor",
        "Società Sportiva Calcio Napoli": "Napoli",
        "Verein für Leibesübungen Wolfsburg": "Wolfsburg",
        "Villarreal Club de Fútbol S.A.D.": "Villarreal",
        "Royal Antwerp Football Club": "Antwerp",
        "AC Ajaccio": "Ajaccio",
        "Parma Calcio 1913": "Parma",
        "Cesena FC": "Cesena",
        "Bayer 04 Leverkusen Fußball": "Bayer Leverkusen",
        "PFK Stal Kamyanske (-2018)": "Stal Kamyanske",
        "FC Vestsjaelland": "Vestsjaelland",
        "Balikesirspor": "Balikesirspor",
        "Orduspor": "Orduspor",
        "SPAL": "SPAL",
        "Verona Hellas Football Club": "Hellas Verona",
        "Futebol Clube de Famalicão": "Famalicão",
        "Tom Tomsk": "Tom Tomsk",
        "Aberdeen Football Club": "Aberdeen",
        "Koninklijke Sint-Truidense Voetbalvereniging": "Sint-Truiden",
        "FC Ingulets Petrove": "Inhulets Petrove",
        "KSC Lokeren (- 2020)": "Lokeren",
        "Gaziantepspor (- 2020)": "Gaziantepspor",
        "Ionikos Nikeas": "Ionikos",
        "De Graafschap Doetinchem": "De Graafschap",
        "A.G.S Asteras Tripolis": "Asteras Tripolis",
        "Nottingham Forest Football Club": "Nottingham Forest",
        "Verein für Leibesübungen Bochum 1848 Fußballgemeinschaft": "VfL Bochum",
        "CF União Madeira (-2021)": "União Madeira",
        "Luton Town": "Luton Town",
        "Wigan Athletic": "Wigan Athletic",
        "Alkmaar Zaanstreek": "AZ Alkmaar",
        "Huddersfield Town": "Huddersfield",
        "Mordovia Saransk (-2020)": "Mordovia Saransk",
        "AS Nancy-Lorraine": "Nancy",
        "Volga Nizhniy Novgorod (- 2016)": "Volga Nizhny Novgorod",
        "CS Marítimo": "Marítimo",
        "Heracles Almelo": "Heracles",
        "Stade de Reims": "Reims",
        "Valenciennes FC": "Valenciennes",
        "Association sportive de Monaco Football Club": "Monaco",
        "Bursaspor": "Bursaspor",
        "Rooms Katholieke Combinatie Waalwijk": "RKC Waalwijk",
        "Eintracht Frankfurt Fußball AG": "Eintracht Frankfurt",
        "Athlitiki Enosi Konstantinoupoleos": "AEK Athens",
        "KV Oostende": "Oostende",
        "Sport Lisboa e Benfica": "Benfica",
        "APS Atromitos Athinon": "Atromitos",
        "Club Atlético Osasuna": "Osasuna",
        "Desportivo Aves (- 2020)": "Aves",
        "Getafe Club de Fútbol S.A.D. Team Dubai": "Getafe",
        "Eindhovense Voetbalvereniging Philips Sport Vereniging": "PSV Eindhoven",
        "Vitesse Arnhem": "Vitesse",
        "AFC Ajax Amsterdam": "Ajax",
        "Metalist Kharkiv (- 2016)": "Metalist",
        "FK Mariupol": "Mariupol",
        "Akron Togliatti": "Akron",
        "FC Sochaux-Montbéliard": "Sochaux",
        "Newcastle United Football Club": "Newcastle",
        "Eskisehirspor": "Eskisehirspor",
        "FK Livyi Bereh": "Livyi Bereh",
        "Olympique Lyonnais": "Lyon",
        "FK Zarya Lugansk": "Zorya Luhansk",
        "Málaga CF": "Málaga",
        "Brentford Football Club": "Brentford",
        "SM Caen": "Caen",
        "Koninklijke Racing Club Genk": "Genk",
        "Torpedo Moscow": "Torpedo",
        "AO Xanthi": "Xanthi",
        "FC Emmen": "Emmen",
        "Real Zaragoza": "Zaragoza",
        "Borussia Dortmund": "Borussia Dortmund",
        "Football Club Groningen": "Groningen",
        "Swansea City": "Swansea",
        "Real Club Deportivo Mallorca S.A.D.": "Mallorca",
        "Sivasspor Kulübü": "Sivasspor",
        "Clube Desportivo Santa Clara": "Santa Clara",
        "Rio Ave Futebol Clube": "Rio Ave",
        "Inverness Caledonian Thistle FC": "Inverness",
        "Panathinaikos Athlitikos Omilos": "Panathinaikos",
        "Gaziantep Futbol Kulübü A.Ş.": "Gaziantep",
        "Fußball-Club St. Pauli von 1910": "St. Pauli",
        "GFC Ajaccio": "Gazélec Ajaccio",
        "AC Carpi": "Carpi",
        "Hannover 96": "Hannover",
        "Middlesbrough FC": "Middlesbrough",
        "Racing Club de Strasbourg Alsace": "Strasbourg",
        "Real Sociedad de Fútbol S.A.D.": "Real Sociedad",
        "Crystal Palace Football Club": "Crystal Palace",
        "Reading FC": "Reading",
        "Queens Park Rangers": "QPR",
        "Club Deportivo Leganés S.A.D.": "Leganés",
        "Thonon Évian Grand Genève FC": "Évian",
        "FK Krasnodar": "Krasnodar",
        "Akhisarspor": "Akhisarspor",
        "Olympique de Marseille": "Marseille",
        "Royal Excel Mouscron (-2022)": "Mouscron",
        "Mersin Talimyurdu SK": "Mersin",
        "SV Zulte Waregem": "Zulte Waregem",
        "Yellow-Red Koninklijke Voetbalclub Mechelen": "Mechelen",
        "Rayo Vallecano de Madrid S.A.D.": "Rayo Vallecano",
        "West Ham United Football Club": "West Ham",
        "US Salernitana 1919": "Salernitana",
        "Willem II": "Willem II",
        "FC Tosno (-2018)": "Tosno",
        "Hamburger SV": "Hamburg",
        "Vejle Boldklub": "Vejle",
        "Randers Fodbold Club": "Randers",
        "Koninklijke Voetbalclub Kortrijk": "Kortrijk",
        "Verein für Bewegungsspiele Stuttgart 1893": "VfB Stuttgart",
        "Sportverein Werder Bremen von 1899": "Werder Bremen",
        "Fulham Football Club": "Fulham",
        "AO FK Zenit Sankt-Peterburg": "Zenit",
        "Norwich City": "Norwich",
        "ADO Den Haag": "Den Haag",
        "Kardemir Karabükspor": "Karabükspor",
        "Elche CF": "Elche",
        "Club Brugge Koninklijke Voetbalvereniging": "Club Brugge",
        "Konyaspor": "Konyaspor",
        "Olimpik Donetsk": "Olimpik Donetsk",
        "Club Football Estrela da Amadora": "Estrela Amadora",
        "FC Rubin Kazan": "Rubin Kazan",
        "Partick Thistle FC": "Partick Thistle",
        "Ankaraspor": "Ankaraspor",
        "Fenerbahçe Spor Kulübü": "Fenerbahçe",
        "Fortuna Sittardia Combinatie": "Fortuna Sittard",
        "Sparta Rotterdam": "Sparta",
        "Paris Saint-Germain Football Club": "PSG",
        "Athletic Club Bilbao": "Athletic Bilbao",
        "SpVgg Greuther Fürth": "Greuther Fürth",
        "Fatih Karagümrük": "Karagümrük",
        "Ipswich Town Football Club": "Ipswich Town",
        "Olympiakos Syndesmos Filathlon Peiraios": "Olympiakos",
        "Almere City Football Club": "Almere City",
        "EA Guingamp": "Guingamp",
        "Istanbulspor": "Istanbulspor",
        "Koninklijke Voetbal Club Westerlo": "Westerlo",
        "Manchester United Football Club": "Manchester United",
        "Alanyaspor": "Alanyaspor",
        "Burnley FC": "Burnley",
        "Go Ahead Eagles": "Go Ahead Eagles",
        "Real Betis Balompié S.A.D.": "Real Betis",
        "Samsunspor": "Samsunspor",
        "Royal Charleroi Sporting Club": "Charleroi",
        "FC Oleksandriya": "Oleksandriya",
        "PFK CSKA Moskva": "CSKA Moscow",
        "Boavista Futebol Clube": "Boavista",
        "NK Veres Rivne": "Veres Rivne",
        "PAS Giannina": "PAS Giannina",
        "Anzhi Makhachkala (-2022)": "Anzhi",
        "FK Ufa": "Ufa",
        "Hamilton Academical FC": "Hamilton Academical",
        "Levante UD": "Levante",
        "Futbolniy Klub Dynamo Kyiv": "Dynamo Kyiv",
        "The Celtic Football Club": "Celtic",
        "Juventus Football Club": "Juventus",
        "Association sportive de Saint-Étienne Loire": "Saint-Étienne",
        "ZAO FK Chornomorets Odessa": "Chornomorets Odessa",
        "Dinamo Makhachkala": "Dinamo Makhachkala",
        "Genclerbirligi Ankara": "Genclerbirligi",
        "FK Rostov": "Rostov",
        "ESTAC Troyes": "Troyes",
        "FK Dinamo Moskva": "Dinamo Moscow",
        "Angers Sporting Club de l'Ouest": "Angers",
        "FK Sevastopol (- 2014)": "Sevastopol",
        "FC Helsingør": "Helsingør",
        "RasenBallsport Leipzig": "RB Leipzig",
        "Ümraniyespor": "Ümraniyespor",
        "Cádiz CF": "Cádiz",
        "PFK Krylya Sovetov Samara": "Krylya Sovetov",
        "Associazione Calcio Monza": "Monza",
        "Football Club Twente": "Twente",
        "Pendikspor": "Pendikspor",
        "Dnipro Dnipropetrovsk (-2020)": "Dnipro",
        "Clermont Foot 63": "Clermont",
        "Società Sportiva Lazio S.p.A.": "Lazio",
        "Benevento Calcio": "Benevento",
        "Real Madrid Club de Fútbol": "Real Madrid",
        "FK Nizhny Novgorod": "Nizhny Novgorod",
        "RWD Molenbeek": "Molenbeek",
        "US Sassuolo": "Sassuolo",
        "CD Tondela": "Tondela",
        "Futebol Clube do Porto": "Porto",
        "Le Havre Athletic Club": "Le Havre",
        "1. FC Union Berlin": "Union Berlin",
        "Real Club Celta de Vigo S. A. D.": "Celta Vigo",
        "Siena FC": "Siena",
        "Cagliari Calcio": "Cagliari",
        "Amiens SC": "Amiens",
        "Göztepe Sportif Yatırımlar A.Ş.": "Göztepe",
        "FC Augsburg 1907": "Augsburg",
        "FK Spartak Moskva": "Spartak Moscow",
        "Vitória Sport Clube": "Vitória SC",
        "Gil Vicente Futebol Clube": "Gil Vicente",
        "Kuban Krasnodar (-2018)": "Kuban Krasnodar",
        "Spartak Vladikavkaz (-2020)": "Spartak Vladikavkaz",
        "Sunderland AFC": "Sunderland",
        "Delfino Pescara 1936": "Pescara",
        "1.FC Köln": "Köln",
        "FK Khimki": "Khimki",
        "Arsenal Tula": "Arsenal Tula",
        "Adana Demirspor Kulübü": "Adana Demirspor",
        "Associazione Calcio Fiorentina": "Fiorentina",
        "Volyn Lutsk": "Volyn Lutsk",
        "FC Rukh Lviv": "Rukh Lviv",
        "Associazione Calcio Milan": "AC Milan",
        "Stoke City": "Stoke City",
        "Hobro IK": "Hobro",
        "Volou Neos Podosferikos Syllogos": "Volos",
        "Aarhus Gymnastik Forening": "Aarhus GF",
        "Hatayspor Futbol Kulübü": "Hatayspor",
        "Racing Club de Lens": "Lens",
        "Zirka Kropyvnytskyi": "Zirka",
        "Deportivo de La Coruña": "Deportivo",
        "Motherwell Football Club": "Motherwell",
        "Viborg Fodsports Forening": "Viborg",
        "Vitória Setúbal FC": "Vitória Setúbal",
        "Arsenal Football Club": "Arsenal",
        "Çaykur Rizespor Kulübü": "Rizespor",
        "Catania FC": "Catania",
        "Granada CF": "Granada",
        "Lierse SK (- 2018)": "Lierse",
        "SK Tavriya Simferopol ( - 2022)": "Tavriya",
        "US Cremonese": "Cremonese",
        "Genoa Cricket and Football Club": "Genoa",
        "Manchester City Football Club": "Man City",
        "UD Almería": "Almería",
        "1. Fußball- und Sportverein Mainz 05": "Mainz 05",
        "PAS Lamia 1964": "Lamia",
        "Aston Villa Football Club": "Aston Villa",
        "Apollon Smyrnis": "Apollon Smyrnis",
        "AOK Kerkyra": "Kerkyra",
        "Wolverhampton Wanderers Football Club": "Wolves",
        "Sport-Club Freiburg": "Freiburg",
        "FC Minaj": "Minaj",
        "LNZ Cherkasy": "Cherkasy",
        "FC Shakhtar Donetsk": "Shakhtar",
        "Kayseri Erciyesspor": "Kayseri Erciyesspor",
        "FC Vizela": "Vizela",
        "Reial Club Deportiu Espanyol de Barcelona S.A.D.": "Espanyol",
        "Excelsior Rotterdam": "Excelsior",
        "Chievo Verona": "Chievo",
        "Frosinone Calcio": "Frosinone",
        "Arsenal Kyiv": "Arsenal Kyiv",
        "Girona Fútbol Club S. A. D.": "Girona",
        "Livingston FC": "Livingston",
        "SC Paderborn 07": "Paderborn",
        "Brescia Calcio": "Brescia",
        "Eintracht Braunschweig": "Braunschweig",
        "FC Schalke 04": "Schalke 04",
        "Sheffield United": "Sheffield Utd",
        "FK Kryvbas Kryvyi Rig": "Kryvbas",
        "Lyngby Boldklubben af 1921": "Lyngby",
        "RFK Akhmat Grozny": "Akhmat Grozny",
        "PFK Tambov (-2021)": "Tambov",
        "Unión Deportiva Las Palmas S.A.D.": "Las Palmas",
        "Cercle Brugge Koninklijke Sportvereniging": "Cercle Brugge",
        "Panetolikos Agrinio": "Panetolikos",
        "Omilos Filathlon Irakliou FC": "OFI",
        "Metalurg Zaporizhya (-2016)": "Metalurg Zaporizhya",
        "Portimonense SC": "Portimonense",
        "FC Verbroedering Denderhoutem Denderleeuw Eendracht Hekelgem": "Dender",
        "Clube Desportivo Nacional": "Nacional",
        "Unione Sportiva Lecce": "Lecce",
        "UC Sampdoria": "Sampdoria",
        "Panthessalonikios Athlitikos Omilos Konstantinoupoliton": "PAOK",
        "Avs Futebol SAD": "Avs",
        "US Livorno 1915": "Livorno",
        "KAS Eupen": "Eupen",
        "VVV-Venlo": "Venlo",
        "SD Eibar": "Eibar",
        "Southampton Football Club": "Southampton",
        "Vendsyssel FF": "Vendsyssel",
        "Feyenoord Rotterdam": "Feyenoord",
        "Altay SK": "Altay",
        "Sporting Gijón": "Sporting Gijón",
        "Baltika Kaliningrad": "Baltika",
        "Metalurg Donetsk (- 2015)": "Metalurg Donetsk",
        "Kayserispor Kulübü": "Kayserispor",
        "CD Feirense": "Feirense",
        "Panserraikos Serres": "Panserraikos",
        "Sevilla Fútbol Club S.A.D.": "Sevilla",
        "Fortuna Düsseldorf": "Fortuna Düsseldorf",
        "Royale Union Saint-Gilloise": "Union SG",
        "Toulouse Football Club": "Toulouse",
        "Torino Calcio": "Torino",
        "Olympique Gymnaste Club Nice Côte d'Azur": "OGC Nice",
        "Hertha BSC": "Hertha BSC",
        "Nijmegen Eendracht Combinatie": "NEC",
        "FK Polissya Zhytomyr": "Polissya",
        "Chelsea Football Club": "Chelsea",
        "Eyüp Spor Kulübü": "Eyüpspor",
        "Empoli Football Club S.r.l.": "Empoli",
        "Denizlispor": "Denizlispor",
        "Fodbold Club Midtjylland": "Midtjylland",
        "Arminia Bielefeld": "Arminia",
        "Kasımpaşa Spor Kulübü": "Kasımpaşa",
        "Valencia Club de Fútbol S. A. D.": "Valencia",
        "Aalborg Boldspilklub": "Aalborg",
        "Sporting Clube de Braga": "Braga",
        "Prins Hendrik Ende Desespereert Nimmer Combinatie Zwolle": "PEC Zwolle",
        "Nooit Opgeven Altijd Doorzetten Aangenaam Door Vermaak En Nuttig Door Ontspanning Combinatie Breda": "NAC Breda",
        "Elazigspor": "Elazigspor",
        "FC Bayern München": "FC Bayern",
        "Ross County Football Club": "Ross County",
        "Fodbold Club Nordsjælland": "Nordsjælland",
        "Everton Football Club": "Everton",
        "Association de la Jeunesse auxerroise": "AJ Auxerre",
        "AE Kifisias": "Kifisia",
        "Sportclub Heerenveen": "Heerenveen",
        "Athens Kallithea Football Club": "Kallithea",
        "Casa Pia Atlético Clube": "Casa Pia",
        "FC Metz": "Metz",
        "Enisey Krasnoyarsk": "Enisey",
        "Leeds United": "Leeds",
        "FC Crotone": "Crotone",
        "Saint Mirren Football Club": "St. Mirren",
        "FK Kolos Kovalivka": "Kolos",
        "TSG 1899 Hoffenheim Fußball-Spielbetriebs GmbH": "Hoffenheim",
        "Royal Sporting Club Anderlecht": "Anderlecht",
        "Venezia Football Club": "Venezia",
        "CF Os Belenenses": "Belenenses",
        "FC Volendam": "FC Volendam",
        "Atalanta Bergamasca Calcio S.p.a.": "Atalanta",
        "FK Karpaty Lviv": "Karpaty",
        "Moreirense Futebol Clube": "Moreirense",
        "West Bromwich Albion": "West Bromwich"
    })

    return club_name_to_shorthand.get(full_name, full_name)
