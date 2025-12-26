import os
import logging
import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

logger = logging.getLogger("CalendarClient")

# Shared environment variables
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

def get_calendar_service():
    """
    Returns a Google Calendar service instance if credentials are available.
    Returns None otherwise.
    """
    # Try loading from token.json first (preferred for automated usage)
    creds = None
    if os.path.exists('token.json'):
        try:
            creds = Credentials.from_authorized_user_file('token.json')
        except Exception as e:
            logger.error(f"Error loading token.json: {e}")
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.error(f"Failed to refresh token: {e}")
                return None
        else:
            # We cannot interactively login here in headless mode.
            logger.warning("📅 Calendar credentials missing or invalid. Interactive login required.")
            return None

    return build('calendar', 'v3', credentials=creds)

def get_next_event(calendar_id='primary', max_results=1):
    """
    Retrieves the next upcoming event from the calendar.
    """
    service = get_calendar_service()
    if not service:
        return None

    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    
    try:
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])
        return events
    except Exception as e:
        logger.error(f"Failed to fetch events: {e}")
        return None

def create_calendar_event(summary, description, start_time, end_time):
    service = get_calendar_service()
    if not service:
        return None

    event = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start_time,
            'timeZone': 'UTC',
        },
        'end': {
            'dateTime': end_time,
            'timeZone': 'UTC',
        },
    }

    try:
        event = service.events().insert(calendarId='primary', body=event).execute()
        logger.info(f"📅 Event created: {event.get('htmlLink')}")
        return event
    except Exception as e:
        logger.error(f"Failed to create event: {e}")
        return None