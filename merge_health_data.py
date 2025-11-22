import json

# Correct paths
audio_file = "vault_files/audio/audio_data.json"
photo_file = "photo_data.json"
health_log_file = "health_log.json"
summary_file = "vault_files/reports/summary_data.json"

# Load JSON files
with open(health_log_file) as f:
    log = json.load(f)

with open(photo_file) as f:
    photos = json.load(f)

with open(audio_file) as f:
    audio = json.load(f)

with open(summary_file) as f:
    summaries = json.load(f)

# Build combined list
combined = []

# Health log entries
for l in log.get("entries", []):
    combined.append({
        "type": "log",
        "text": l.get("text", ""),
        "timestamp": l.get("timestamp", "")
    })

# Photos
for p in photos.get("photos", []):
    combined.append({
        "type": "photo",
        "filename": p.get("file", ""),
        "stored_as": p.get("file", ""),
        "timestamp": p.get("timestamp", "")
    })

# Audio notes
for a in audio.get("audio", []):
    combined.append({
        "type": "audio",
        "filename": a.get("file", ""),
        "stored_as": a.get("file", ""),
        "timestamp": a.get("timestamp", "")
    })

# Summaries
for s in summaries.get("summaries", []):
    combined.append({
        "type": "summary",
        "text": s.get("text", ""),
        "timestamp": s.get("timestamp", "")
    })

# Save final merged file
final = {"data": combined}

with open("health_data.json", "w") as f:
    json.dump(final, f, indent=4)

print("\n✔ Merged health_data.json created successfully!\n")
