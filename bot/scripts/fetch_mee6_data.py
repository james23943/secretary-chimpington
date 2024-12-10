import requests
import json

def fetch_mee6_data():
    server_id = "913372558693396511"
    page = 0
    all_data = []
    
    while True:
        url = f"https://mee6.xyz/api/plugins/levels/leaderboard/{server_id}?page={page}"
        response = requests.get(url)
        
        if response.status_code != 200:
            print(f"Error fetching page {page}")
            break
            
        data = response.json()
        players = data.get('players', [])
        
        if not players:
            break
            
        # Filter only needed data
        filtered_players = [{
            'id': player['id'],
            'message_count': player['message_count']
        } for player in players]
            
        all_data.extend(filtered_players)
        page += 1
        print(f"Fetched page {page}")
    
    # Save to file
    with open('mee6_levels.json', 'w') as f:
        json.dump(all_data, f, indent=4)
    
    print(f"Saved {len(all_data)} user records")

if __name__ == "__main__":
    fetch_mee6_data()