from flask import Flask, render_template
from events import fetch_events
from s3_helper import upload_image_to_s3
import schedule
import time
import threading

app = Flask(__name__)

# Global list to hold current events
cached_events = []

def refresh_events():
    """Fetch events from Ticketmaster and upload images to S3."""
    global cached_events
    print("Fetching events from Ticketmaster...")
    events = fetch_events()
    for event in events:
        # Upload each event image to S3 and replace URL with S3 URL
        if event.get("image_url"):
            s3_url = upload_image_to_s3(event["image_url"], event["id"])
            if s3_url:
                event["image_url"] = s3_url
    cached_events = events
    print(f"Refreshed {len(cached_events)} events.")

@app.route("/")
def index():
    """Main page — show all university events."""
    return render_template("index.html", events=cached_events)

def start_scheduler():
    """Run event refresh every 30 minutes in background."""
    schedule.every(30).minutes.do(refresh_events)
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    # Fetch events once on startup
    refresh_events()
    # Start background scheduler thread
    t = threading.Thread(target=start_scheduler, daemon=True)
    t.start()
    # Run Flask on port 5000
    app.run(host="0.0.0.0", port=5000)
