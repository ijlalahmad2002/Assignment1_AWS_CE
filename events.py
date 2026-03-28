import requests
import os

# Replace with your actual Ticketmaster API key
TICKETMASTER_API_KEY = os.environ.get("TICKETMASTER_API_KEY", "YOUR_API_KEY_HERE")
TICKETMASTER_URL = "https://app.ticketmaster.com/discovery/v2/events.json"

def fetch_events(size=20):
    """
    Fetch events from Ticketmaster Discovery API.
    Returns a list of simplified event dictionaries.
    """
    params = {
        "apikey": TICKETMASTER_API_KEY,
        "size": size,
        "sort": "date,asc"
    }

    try:
        response = requests.get(TICKETMASTER_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        events = []
        raw_events = data.get("_embedded", {}).get("events", [])

        for item in raw_events:
            # Extract event details safely
            event_id = item.get("id", "unknown")
            name = item.get("name", "Untitled Event")

            # Date
            date_info = item.get("dates", {}).get("start", {})
            date = date_info.get("localDate", "TBA")
            time_ = date_info.get("localTime", "")

            # Venue
            venues = item.get("_embedded", {}).get("venues", [])
            venue = venues[0].get("name", "Unknown Venue") if venues else "Unknown Venue"
            city = venues[0].get("city", {}).get("name", "") if venues else ""

            # Description
            description = item.get("info") or item.get("pleaseNote") or "No description available."

            # Image — pick the widest one
            images = item.get("images", [])
            image_url = ""
            if images:
                best = max(images, key=lambda x: x.get("width", 0))
                image_url = best.get("url", "")

            events.append({
                "id": event_id,
                "name": name,
                "date": date,
                "time": time_,
                "venue": venue,
                "city": city,
                "description": description[:300],  # limit length
                "image_url": image_url
            })

        return events

    except requests.exceptions.RequestException as e:
        print(f"Error fetching events: {e}")
        return []
