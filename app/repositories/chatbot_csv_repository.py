from sqlalchemy.orm import Session
from app.entities.chatbot_csv_entity import ChatbotCsvEntity


def create_csv_record(
    db: Session,
    chatbot_id: int,
    gcs_url: str,
    original_filename: str,
) -> ChatbotCsvEntity:
    record = ChatbotCsvEntity(
        chatbot_id=chatbot_id,
        gcs_url=gcs_url,
        original_filename=original_filename,
    )
    db.add(record)
    db.flush()
    return record
