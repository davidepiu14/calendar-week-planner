#!/usr/bin/env python3
import datetime
import pickle
import os.path
from zoneinfo import ZoneInfo
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']
TIMEZONE = "Europe/Rome"  # Timezone set to Rome

# Define the weekly schedule with English categories.
schedule = {
    "Monday": [
        {"start": "05:30", "end": "08:00", "category": "Training"},
        {"start": "08:00", "end": "09:00", "category": "Personal"},
        {"start": "09:00", "end": "13:00", "category": "Work"},
        {"start": "13:00", "end": "14:00", "category": "Personal"},
        {"start": "14:00", "end": "18:00", "category": "Work"},
        {"start": "18:00", "end": "19:30", "category": "Study"},
        {"start": "19:30", "end": "20:30", "category": "Networking"},
    ],
    "Tuesday": [
        {"start": "05:30", "end": "08:00", "category": "Training"},
        {"start": "08:00", "end": "09:00", "category": "Personal"},
        {"start": "09:00", "end": "13:00", "category": "Work"},
        {"start": "13:00", "end": "14:00", "category": "Personal"},
        {"start": "14:00", "end": "18:00", "category": "Work"},
        {"start": "18:00", "end": "19:30", "category": "Upskilling"},
        {"start": "19:30", "end": "20:30", "category": "Networking"},
    ],
    "Wednesday": [
        {"start": "05:30", "end": "08:00", "category": "Training"},
        {"start": "08:00", "end": "09:00", "category": "Personal"},
        {"start": "09:00", "end": "13:00", "category": "Work"},
        {"start": "13:00", "end": "14:00", "category": "Personal"},
        {"start": "14:00", "end": "18:00", "category": "Work"},
        {"start": "18:00", "end": "19:30", "category": "Upskilling"},
        {"start": "19:30", "end": "20:30", "category": "Networking"},
    ],
    "Thursday": [
        {"start": "05:30", "end": "08:00", "category": "Training"},
        {"start": "08:00", "end": "09:00", "category": "Personal"},
        {"start": "09:00", "end": "13:00", "category": "Work"},
        {"start": "13:00", "end": "14:00", "category": "Personal"},
        {"start": "14:00", "end": "18:00", "category": "Work"},
        {"start": "18:00", "end": "19:30", "category": "Study"},
        {"start": "19:30", "end": "20:30", "category": "Networking"},
    ],
    "Friday": [
        {"start": "05:30", "end": "08:00", "category": "Training"},
        {"start": "08:00", "end": "09:00", "category": "Personal"},
        {"start": "09:00", "end": "13:00", "category": "Work"},
        {"start": "13:00", "end": "14:00", "category": "Personal"},
        {"start": "14:00", "end": "18:00", "category": "Work"},
        {"start": "18:00", "end": "19:30", "category": "Upskilling"},
        {"start": "19:30", "end": "20:30", "category": "Networking"},
    ],
    "Saturday": [
        {"start": "06:00", "end": "10:00", "category": "Training"},
        {"start": "10:00", "end": "12:00", "category": "Study"},
        {"start": "12:00", "end": "14:00", "category": "Personal"},
        {"start": "14:00", "end": "16:00", "category": "Upskilling"},
    ],
    "Sunday": [
        {"start": "07:00", "end": "09:00", "category": "Training"},
        {"start": "09:00", "end": "10:00", "category": "Training"},
        {"start": "10:00", "end": "11:00", "category": "Personal"},
    ]
}

# Mapping of categories to Google Calendar color IDs (strings from "1" to "11")
color_mapping = {
    "Training": "11",   # Tomato (red)
    "Personal": "3",    # Grape (purple)
    "Work": "9",        # Blueberry (blue)
    "Study": "2",       # Sage (green)
    "Upskilling": "5",  # Banana (yellow)
    "Networking": "6"   # Tangerine (orange)
}


def get_next_weekday(day_name: str) -> datetime.date:
    """
    Returns the date of the next occurrence of the specified weekday (e.g., 'Monday').
    """
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


def get_or_create_calendar(service):
    """
    Checks for an existing calendar with the summary "Weekly Schedule".
    If found, returns its calendar ID; otherwise, creates a new calendar.
    """
    calendar_list = service.calendarList().list().execute()
    for calendar in calendar_list.get('items', []):
        if calendar.get('summary') == "Weekly Schedule":
            print("Using existing 'Weekly Schedule' calendar with ID:",
                  calendar['id'])
            return calendar['id']
    # Create new calendar if not found.
    calendar_body = {'summary': 'Weekly Schedule', 'timeZone': TIMEZONE}
    created_calendar = service.calendars().insert(body=calendar_body).execute()
    print("Created new calendar with ID:", created_calendar['id'])
    return created_calendar['id']


def main():
    creds = None
    # Load saved credentials if they exist.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no valid credentials available, prompt the user to log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for future runs.
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    calendar_id = get_or_create_calendar(service)

    # For each day, create or update recurring weekly events.
    for day, events in schedule.items():
        event_date = get_next_weekday(day)
        for ev in events:
            # Generate a unique key for the event.
            event_key = f"{day}_{ev['start']}_{ev['end']}_{ev['category']}"

            # Parse the start and end times.
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

            # Check if an event with the same unique key already exists.
            query = service.events().list(
                calendarId=calendar_id,
                privateExtendedProperty=f"weeklyScheduleId={event_key}"
            ).execute()

            if query.get('items'):
                print(
                    f"Event '{event_key}' already exists. Skipping creation.")
                continue  # Skip creating this event

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
                # Set the event to recur weekly.
                'recurrence': ['RRULE:FREQ=WEEKLY'],
                # Store the unique key in the event's private extended properties.
                'extendedProperties': {
                    'private': {
                        'weeklyScheduleId': event_key
                    }
                }
            }
            # Add a color based on the event category.
            color = color_mapping.get(ev['category'])
            if color:
                event_body['colorId'] = color

            created_event = service.events().insert(
                calendarId=calendar_id, body=event_body).execute()
            print(
                f"Created event: {created_event.get('summary')} ({day} {ev['start']}-{ev['end']})")


if __name__ == '__main__':
    main()
