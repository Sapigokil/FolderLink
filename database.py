import os
import json

DB_FILE = os.path.join(os.getenv('APPDATA'), 'LinkManager_History.json')

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_to_db(source, destination):
    data = load_db()
    data.append({
        "source": source,
        "destination": destination
    })
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def delete_from_db(source, destination):
    data = load_db()
    new_data = [item for item in data if not (item['source'] == source and item['destination'] == destination)]
    with open(DB_FILE, 'w') as f:
        json.dump(new_data, f, indent=4)