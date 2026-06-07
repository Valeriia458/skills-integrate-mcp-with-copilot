"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from datetime import datetime, time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}

# In-memory schedule entries for lesson and extra events
schedule_entries = []
ALLOWED_DAYS = {
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
}
MAX_DAILY_LIMITS = {
    "lesson": 12,
    "extra": 6
}


class ScheduleEntry(BaseModel):
    type: str
    day: str
    start_time: str
    end_time: str
    name: str
    location: str = ""


def parse_time(value: str) -> time:
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid time format: {value}. Use HH:MM.")


def times_overlap(start_a: time, end_a: time, start_b: time, end_b: time) -> bool:
    return start_a < end_b and start_b < end_a


def validate_schedule_entry(entry: ScheduleEntry):
    entry_type = entry.type.lower()
    if entry_type not in MAX_DAILY_LIMITS:
        raise HTTPException(status_code=400, detail="Type must be 'lesson' or 'extra'.")

    if entry.day not in ALLOWED_DAYS:
        raise HTTPException(status_code=400, detail="Day must be one of Monday through Sunday.")

    start = parse_time(entry.start_time)
    end = parse_time(entry.end_time)
    if start >= end:
        raise HTTPException(status_code=400, detail="Start time must be before end time.")

    same_day_entries = [
        existing for existing in schedule_entries
        if existing["day"] == entry.day and existing["type"] == entry_type
    ]

    if len(same_day_entries) >= MAX_DAILY_LIMITS[entry_type]:
        raise HTTPException(
            status_code=400,
            detail=f"Daily limit reached for {entry_type}s on {entry.day}."
        )

    for existing in same_day_entries:
        existing_start = parse_time(existing["start_time"])
        existing_end = parse_time(existing["end_time"])
        if times_overlap(start, end, existing_start, existing_end):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"The new {entry_type} overlaps with an existing {entry_type} "
                    f"from {existing['start_time']} to {existing['end_time']} on {entry.day}."
                )
            )


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}


@app.get("/schedule/entries")
def get_schedule_entries():
    return schedule_entries


@app.post("/schedule/entries")
def add_schedule_entry(entry: ScheduleEntry):
    """Add a schedule entry with validation for overlaps and daily limits."""
    validate_schedule_entry(entry)
    schedule_entries.append(entry.dict())
    return {
        "message": f"Added {entry.type} '{entry.name}' on {entry.day}.",
        "entry": entry.dict()
    }
