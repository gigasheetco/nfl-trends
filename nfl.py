from pytrends.request import TrendReq
import pandas as pd
import time
from datetime import datetime
import requests

# Initialize pytrends with a longer timeout (e.g., 30 seconds)
pytrends = TrendReq(hl='en-US', tz=-300, timeout=(10, 30))  # Increased timeout

# List of all NFL teams (Team names only, without city)
nfl_teams = [
    "Cardinals", "Falcons", "Ravens", "Bills", "Panthers", "Bears", "Bengals", "Browns",
    "Cowboys", "Broncos", "Lions", "Packers", "Texans", "Colts", "Jaguars", "Chiefs",
    "Raiders", "Chargers", "Rams", "Dolphins", "Vikings", "Patriots", "Saints", "Giants",
    "Jets", "Eagles", "Steelers", "49ers", "Seahawks", "Buccaneers", "Titans", "Commanders"
]

# Common search phrases to append to each team name
search_suffixes = ['news', 'score', 'schedule', 'injuries']  # Added 'injuries'

# Function to handle retries when hitting 429 errors
def fetch_with_retry(func, max_retries=3, wait_time=60):
    retries = 0
    while retries < max_retries:
        try:
            return func()
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 429:
                print(f"Received HTTP 429 error. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                retries += 1
            else:
                raise err
    print(f"Max retries exceeded after {max_retries} attempts.")
    return None

# Function to get Google Trends data for each NFL team with batched search terms
def get_trends(teams, suffixes, timeframe='now 7-d', geo='US'):
    trends_data = pd.DataFrame()

    for team in teams:
        # Create search terms with just the team name + suffixes
        search_terms = [f"{team} {suffix}" for suffix in suffixes]
        
        def fetch_trends():
            pytrends.build_payload(search_terms, cat=0, timeframe=timeframe, geo=geo, gprop='')
            return pytrends.interest_over_time()

        print(f"Fetching data for: {team} with terms {search_terms}")
        team_trend = fetch_with_retry(fetch_trends)

        if team_trend is not None and not team_trend.empty:
            # Create a dataframe where each search term is in its own column
            team_trend['Team'] = team
            team_trend = team_trend.reset_index()  # To expose the datetime column

            # Rename columns for clarity
            team_trend.rename(columns={
                search_terms[0]: 'Searches for News',
                search_terms[1]: 'Searches for Score',
                search_terms[2]: 'Searches for Schedule',
                search_terms[3]: 'Searches for Injuries'
            }, inplace=True)

            # Use pd.concat to collect the data
            trends_data = pd.concat([trends_data, team_trend], axis=0)

        # Respect rate limits by adding a delay
        time.sleep(5)  # Increased delay to avoid rate limiting issues

    return trends_data

# Fetch weekly search trends for all NFL teams with additional terms
nfl_trends = get_trends(nfl_teams, search_suffixes)

# Reorganize columns to match the required format
nfl_trends = nfl_trends[['Team', 'date', 'Searches for News', 'Searches for Score', 'Searches for Schedule', 'Searches for Injuries']]

# Get today's date in MM-DD format
today_date = datetime.today().strftime('%m-%d')

# Save the cleaned data to a CSV file with today's date
output_filename = f'nfl_trends_{today_date}.csv'
nfl_trends.to_csv(output_filename, index=False)

print(f"Search trend data saved to {output_filename}")
