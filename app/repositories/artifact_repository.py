import uuid
from typing import Optional
from sqlalchemy.orm import Session
from app.entities.artifact_entity import ArtifactEntity, ArtifactType


def get_artifact_by_id(
    db: Session,
    artifact_id: uuid.UUID,
    message_id: uuid.UUID,
) -> ArtifactEntity | None:
    return (
        db.query(ArtifactEntity)
        .filter(
            ArtifactEntity.id == artifact_id,
            ArtifactEntity.message_id == message_id,
        )
        .first()
    )


def create_artifact(
    db: Session,
    thread_id: uuid.UUID,
    message_id: uuid.UUID,
    type: ArtifactType,
    title: str,
    spec_json: dict | None,
    data_json: list | None,
    storage_url: str | None = None,
) -> ArtifactEntity:
    artifact = ArtifactEntity(
        thread_id=thread_id,
        message_id=message_id,
        type=type,
        title=title,
        spec_json=spec_json,
        data_json=data_json,
        storage_url=storage_url,
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)
    return artifact
