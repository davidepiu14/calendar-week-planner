# Google Calendar Weekly Schedule Script with Override Logic

This Python script uses the Google Calendar API to create or update a recurring weekly schedule in a calendar named **"Weekly Schedule"**. It prevents duplicate events by using a unique key stored as a private extended property. The script also maps category names (both Italian and English) to canonical English values, and assigns a specific color to each canonical category.

## Features

- **Recurring Events:** Each event is set to recur weekly.
- **Override Logic:** If an event with the same unique key already exists, it is updated instead of creating a duplicate.
- **Canonical Category Mapping:** Italian and English category names are normalized to canonical English names.
- **Color Coding:** Events are color-coded based on their canonical category.
- **TimeZone:** The timezone is set to Europe/Rome.
- **No Deletion Logic:** The script does not include any logic for deleting existing Italian events.

## Prerequisites

- **Python 3.7+**
- **Google Cloud Project:** Create a project in the [Google Cloud Console](https://console.cloud.google.com/), enable the Google Calendar API, and set up OAuth credentials.
- **`credentials.json`:** Download your OAuth client credentials JSON file, rename it to `credentials.json`, and place it in the same folder as the script.
- **Required Python Packages:** Install the necessary packages by running:
  ```bash
  pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
