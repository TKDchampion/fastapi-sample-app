import logging
import os
from fastapi import HTTPException, UploadFile
from google.cloud import storage
from uuid import uuid4
from datetime import datetime, timezone
from google.api_core.exceptions import GoogleAPIError
from app.domain.exception.domain_exception import DomainException

BUCKET_NAME = os.getenv("BUCKET_NAME")
ORG_LOGO_FOLDER = "org_logos"
CHATBOT_CSV_FOLDER = "chatbot/csv_files"


logger = logging.getLogger(__name__)


def upload_logo_to_gcs(file: UploadFile) -> str:
    """
    Upload organization logo to GCS and return public URL.

    Example returned URL:
      https://storage.googleapis.com/adnex-bi/org_logos/20251112/uuid.png
    """
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)

        ext = file.filename.split(".")[-1] if "." in file.filename else "png"
        blob_name = f"{ORG_LOGO_FOLDER}/{datetime.now(timezone.utc).strftime('%Y%m%d')}/{uuid4()}.{ext}"

        blob = bucket.blob(blob_name)
        blob.upload_from_file(file.file, content_type=file.content_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_name}"
        return public_url

    except GoogleAPIError as e:
        logger.error("GCS API error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=502,
            detail={"type": "gcs_error", "msg": f"GCS upload failed: {str(e)}"},
        )

    except Exception as e:
        logger.error("Unexpected error during GCS upload: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"type": "upload_error", "msg": f"Unexpected error: {str(e)}"},
        )


def upload_csv_to_gcs(file: UploadFile) -> str:
    """
    Upload CSV file to GCS and return public URL.

    Example returned URL:
      https://storage.googleapis.com/adnex-bi/chatbot/csv_files/20260407/uuid.csv
    """
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext != "csv":
        raise DomainException(
            msg="Only .csv files are allowed",
            type="invalid_file_type",
            code=400,
        )

    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)

        blob_name = f"{CHATBOT_CSV_FOLDER}/{datetime.now(timezone.utc).strftime('%Y%m%d')}/{uuid4()}.csv"
        blob = bucket.blob(blob_name)
        blob.upload_from_file(file.file, content_type="text/csv")

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_name}"
        return public_url

    except GoogleAPIError as e:
        logger.error("GCS API error during CSV upload: %s", e, exc_info=True)
        raise DomainException(
            msg=f"GCS upload failed: {str(e)}",
            type="gcs_error",
            code=502,
        )

    except DomainException:
        raise

    except Exception as e:
        logger.error("Unexpected error during CSV GCS upload: %s", e, exc_info=True)
        raise DomainException(
            msg=f"Unexpected error: {str(e)}",
            type="upload_error",
            code=500,
        )
