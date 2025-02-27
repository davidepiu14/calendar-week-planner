#!/usr/bin/env python3
import datetime
import pickle
import os.path
from zoneinfo import ZoneInfo
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# If modifying these scopes, delete the token.pickle file.
SCOPES = ['https://www.googleapis.com/auth/calendar']
TIMEZONE = "Europe/Rome"  # Set your desired timezone

# Define the weekly schedule: for each day (in English) a list of events.
# Each event is defined by a start time, end time, and category (used as the event summary).
schedule = {
    "Monday": [
        {"start": "05:30", "end": "08:00", "category": "Workout"},
        {"start": "08:00", "end": "09:00", "category": "Personal"},
        {"start": "09:00", "end": "13:00", "category": "Work"},
        {"start": "13:00", "end": "14:00", "category": "Personal"},
        {"start": "14:00", "end": "18:00", "category": "Work"},
        {"start": "18:00", "end": "19:30", "category": "Study"},
        {"start": "19:30", "end": "20:30", "category": "Networking"},
    ],
    "Tuesday": [
        {"start": "05:30", "end": "08:00", "category": "Workout"},
        {"start": "08:00", "end": "09:00", "category": "Personal"},
        {"start": "09:00", "end": "13:00", "category": "Work"},
        {"start": "13:00", "end": "14:00", "category": "Personal"},
        {"start": "14:00", "end": "18:00", "category": "Work"},
        {"start": "18:00", "end": "19:30", "category": "Upskilling"},
        {"start": "19:30", "end": "20:30", "category": "Networking"},
    ],
    "Wednesday": [
        {"start": "05:30", "end": "08:00", "category": "Workout"},
        {"start": "08:00", "end": "09:00", "category": "Personal"},
        {"start": "09:00", "end": "13:00", "category": "Work"},
        {"start": "13:00", "end": "14:00", "category": "Personal"},
        {"start": "14:00", "end": "18:00", "category": "Work"},
        {"start": "18:00", "end": "19:30", "category": "Upskilling"},
        {"start": "19:30", "end": "20:30", "category": "Networking"},
    ],
    "Thursday": [
        {"start": "05:30", "end": "08:00", "category": "Workout"},
        {"start": "08:00", "end": "09:00", "category": "Personal"},
        {"start": "09:00", "end": "13:00", "category": "Work"},
        {"start": "13:00", "end": "14:00", "category": "Personal"},
        {"start": "14:00", "end": "18:00", "category": "Work"},
        {"start": "18:00", "end": "19:30", "category": "Study"},
        {"start": "19:30", "end": "20:30", "category": "Networking"},
    ],
    "Friday": [
        {"start": "05:30", "end": "08:00", "category": "Workout"},
        {"start": "08:00", "end": "09:00", "category": "Personal"},
        {"start": "09:00", "end": "13:00", "category": "Work"},
        {"start": "13:00", "end": "14:00", "category": "Personal"},
        {"start": "14:00", "end": "18:00", "category": "Work"},
        {"start": "18:00", "end": "19:30", "category": "Upskilling"},
        {"start": "19:30", "end": "20:30", "category": "Networking"},
    ],
    "Saturday": [
        {"start": "06:00", "end": "10:00", "category": "Workout"},
        {"start": "10:00", "end": "12:00", "category": "Study"},
        {"start": "12:00", "end": "14:00", "category": "Personal"},
        {"start": "14:00", "end": "16:00", "category": "Upskilling"},
    ],
    "Sunday": [
        {"start": "07:00", "end": "09:00", "category": "Workout"},
        {"start": "09:00", "end": "10:00", "category": "Workout"},
        {"start": "10:00", "end": "11:00", "category": "Personal"},
    ]
}


def get_next_weekday(day_name: str) -> datetime.date:
    """Return the date of the next occurrence of the specified weekday (e.g., 'Monday')."""
    weekday_map = {
        "Monday": 0,
        "Tuesday": 1,
        "Wednesday": 2,
        "Thursday": 3,
        "Friday": 4,
        "Saturday": 5,
        "Sunday": 6
    }
    today = datetime.date.today()
    target = weekday_map[day_name]
    days_ahead = target - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return today + datetime.timedelta(days=days_ahead)


def main():
    creds = None
    # Load saved credentials if available
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If no valid credentials are available, start the OAuth2 flow.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run.
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    # Create a new calendar for the weekly schedule
    calendar_body = {
        'summary': 'Weekly Schedule',
        'timeZone': TIMEZONE
    }
    created_calendar = service.calendars().insert(body=calendar_body).execute()
    calendar_id = created_calendar['id']
    print("Created new calendar with ID:", calendar_id)

    # For each day, create recurring weekly events
    for day, events in schedule.items():
        event_date = get_next_weekday(day)
        for ev in events:
            # Parse the start and end times
            start_hour, start_minute = map(int, ev['start'].split(':'))
            end_hour, end_minute = map(int, ev['end'].split(':'))
            start_dt = datetime.datetime.combine(
                event_date,
                datetime.time(start_hour, start_minute,
                              tzinfo=ZoneInfo(TIMEZONE))
            )
            end_dt = datetime.datetime.combine(
                event_date,
                datetime.time(end_hour, end_minute, tzinfo=ZoneInfo(TIMEZONE))
            )
            event_body = {
                'summary': ev['category'],
                'start': {
                    'dateTime': start_dt.isoformat(),
                    'timeZone': TIMEZONE,
                },
                'end': {
                    'dateTime': end_dt.isoformat(),
                    'timeZone': TIMEZONE,
                },
                # Set the event to recur weekly
                'recurrence': [
                    'RRULE:FREQ=WEEKLY'
                ]
            }
            created_event = service.events().insert(
                calendarId=calendar_id, body=event_body).execute()
            print(
                f"Created event: {created_event.get('summary')} ({day} {ev['start']}-{ev['end']})")


if __name__ == '__main__':
    main()
