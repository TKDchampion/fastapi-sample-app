from typing import List, Set
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.entities.chatbot_csv_entity import ChatbotCsvEntity


def get_csvs_by_chatbot_id(db: Session, chatbot_id: int) -> List[ChatbotCsvEntity]:
    return (
        db.query(ChatbotCsvEntity)
        .filter(ChatbotCsvEntity.chatbot_id == chatbot_id)
        .all()
    )


def get_latest_failed_csvs_by_chatbot_id(
    db: Session, chatbot_id: int
) -> List[ChatbotCsvEntity]:
    """取每個 original_filename 最新一筆，並 filter is_success = False"""
    subq = (
        db.query(func.max(ChatbotCsvEntity.id).label("max_id"))
        .filter(ChatbotCsvEntity.chatbot_id == chatbot_id)
        .group_by(ChatbotCsvEntity.original_filename)
        .subquery()
    )
    return (
        db.query(ChatbotCsvEntity)
        .join(subq, ChatbotCsvEntity.id == subq.c.max_id)
        .filter(ChatbotCsvEntity.is_success == False)
        .all()
    )


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


def mark_csvs_success(
    db: Session, chatbot_id: int, success_table_names: Set[str]
) -> None:
    """將 success_table_names 對應的最新失敗 CSV 記錄標記為 is_success=True"""
    csvs = get_latest_failed_csvs_by_chatbot_id(db, chatbot_id)
    for csv in csvs:
        table_name = csv.original_filename.rsplit(".", 1)[0]
        if table_name in success_table_names:
            csv.is_success = True
    db.flush()
