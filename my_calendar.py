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

# Canonical mapping: both Italian and English map to the canonical English value.
canonical_categories = {
    "Training": "Training",
    "Allenamento": "Training",
    "Personal": "Personal",
    "Personale": "Personal",
    "Work": "Work",
    "Lavoro": "Work",
    "Study": "Study",
    "Studio": "Study",
    "Upskilling": "Upskilling",
    "Networking": "Networking"
}


def normalize_category(cat):
    return canonical_categories.get(cat, cat)


# Define the weekly schedule (using English category names).
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

# Mapping of canonical categories to Google Calendar color IDs.
color_mapping = {
    "Training": "11",   # Tomato (red)
    "Personal": "3",    # Grape (purple)
    "Work": "9",        # Blueberry (blue)
    "Study": "2",       # Sage (green)
    "Upskilling": "5",  # Banana (yellow)
    "Networking": "6"   # Tangerine (orange)
}


def get_next_weekday(day_name: str) -> datetime.date:
    weekday_map = {
        "Monday": 0, "Tuesday": 1, "Wednesday": 2,
        "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6
    }
    today = datetime.date.today()
    target = weekday_map[day_name]
    days_ahead = target - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return today + datetime.timedelta(days=days_ahead)


def get_or_create_calendar(service):
    calendar_list = service.calendarList().list().execute()
    for calendar in calendar_list.get('items', []):
        if calendar.get('summary') == "Weekly Schedule":
            print("Using existing 'Weekly Schedule' calendar with ID:",
                  calendar['id'])
            return calendar['id']
    calendar_body = {'summary': 'Weekly Schedule', 'timeZone': TIMEZONE}
    created_calendar = service.calendars().insert(body=calendar_body).execute()
    print("Created new calendar with ID:", created_calendar['id'])
    return created_calendar['id']


def find_existing_event(service, calendar_id, event_key, scheduled_day, scheduled_start, normalized):
    # Try extended property lookup.
    query = service.events().list(
        calendarId=calendar_id,
        privateExtendedProperty=f"weeklyScheduleId={event_key}",
        showDeleted=False,
        singleEvents=False
    ).execute()
    if query.get('items'):
        return query.get('items')[0]

    # Search within a time window for a recurring event matching the day, start time, and normalized summary.
    now = datetime.datetime.now(tz=ZoneInfo(TIMEZONE))
    time_min = (now - datetime.timedelta(days=7)).isoformat()
    time_max = (now + datetime.timedelta(days=14)).isoformat()
    events_in_window = service.events().list(
        calendarId=calendar_id,
        timeMin=time_min,
        timeMax=time_max,
        showDeleted=False,
        singleEvents=False
    ).execute()
    for event in events_in_window.get('items', []):
        if 'recurrence' not in event:
            continue
        if not any("RRULE" in rec for rec in event['recurrence']):
            continue
        if 'dateTime' not in event.get('start', {}):
            continue
        try:
            event_start = datetime.datetime.fromisoformat(
                event['start']['dateTime'])
        except Exception:
            continue
        if event_start.strftime("%A") != scheduled_day:
            continue
        if event_start.time().strftime("%H:%M") != scheduled_start:
            continue
        if normalize_category(event.get('summary', '')) != normalized:
            continue
        return event
    return None


def main():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    calendar_id = get_or_create_calendar(service)

    # Process each day in the schedule.
    for day, events in schedule.items():
        event_date = get_next_weekday(day)
        for ev in events:
            normalized = normalize_category(ev['category'])
            event_key = f"{day}_{ev['start']}_{ev['end']}_{normalized}"

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

            existing_event = find_existing_event(
                service, calendar_id, event_key, day, ev['start'], normalized)
            if existing_event:
                update_body = {
                    'summary': normalized,
                    'extendedProperties': {
                        'private': {
                            'weeklyScheduleId': event_key
                        }
                    }
                }
                service.events().patch(
                    calendarId=calendar_id,
                    eventId=existing_event['id'],
                    body=update_body
                ).execute()
                print(f"Event '{event_key}' exists. Updated existing event.")
                continue

            event_body = {
                'summary': normalized,
                'start': {
                    'dateTime': start_dt.isoformat(),
                    'timeZone': TIMEZONE,
                },
                'end': {
                    'dateTime': end_dt.isoformat(),
                    'timeZone': TIMEZONE,
                },
                'recurrence': ['RRULE:FREQ=WEEKLY'],
                'extendedProperties': {
                    'private': {
                        'weeklyScheduleId': event_key
                    }
                }
            }
            color = color_mapping.get(normalized)
            if color:
                event_body['colorId'] = color

            created_event = service.events().insert(
                calendarId=calendar_id, body=event_body).execute()
            print(
                f"Created event: {created_event.get('summary')} ({day} {ev['start']}-{ev['end']})")


if __name__ == '__main__':
    main()
