import logging
import os
from typing import List, Dict, Any, Optional
from google.oauth2.service_account import Credentials
import gspread

logger = logging.getLogger(__name__)

SERVICE_ACCOUNT_FILE = os.getenv(
    "GOOGLE_SHEET_SERVICE_ACCOUNT_FILE", "kddr-demo.service-account.json"
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


def get_gspread_client() -> gspread.Client:
    """
    Get authenticated gspread client using service account.
    """
    credentials = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return gspread.authorize(credentials)


def get_sheet_as_dicts(
    spreadsheet_id: str,
    sheet_name: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Read data from a Google Sheet and return as list of dictionaries.
    Uses first row as headers.

    Args:
        spreadsheet_id: The ID of the spreadsheet (from the URL)
        sheet_name: Optional name of the specific sheet/tab. If None, uses first sheet.

    Returns:
        List of dictionaries, where keys are column headers.
    """
    try:
        client = get_gspread_client()
        spreadsheet = client.open_by_key(spreadsheet_id)

        if sheet_name:
            worksheet = spreadsheet.worksheet(sheet_name)
        else:
            worksheet = spreadsheet.sheet1

        return worksheet.get_all_records()

    except gspread.exceptions.SpreadsheetNotFound:
        logger.error("Spreadsheet not found: %s", spreadsheet_id)
        raise ValueError(f"Spreadsheet not found: {spreadsheet_id}")

    except gspread.exceptions.WorksheetNotFound:
        logger.error("Worksheet not found: %s", sheet_name)
        raise ValueError(f"Worksheet not found: {sheet_name}")

    except gspread.exceptions.APIError as e:
        logger.error("Google Sheets API error: %s", e, exc_info=True)
        raise RuntimeError(f"Google Sheets API error: {str(e)}")

    except Exception as e:
        logger.error("Unexpected error reading Google Sheet: %s", e, exc_info=True)
        raise RuntimeError(f"Unexpected error: {str(e)}")
