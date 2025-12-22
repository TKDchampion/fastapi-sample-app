from sqlalchemy.orm import Session
from app.decorators.db_transaction import db_tx
from app.dtos.business_module_dto import BusinessModuleDTO
from app.repositories import business_module_repository


@db_tx
def get_business_module(db: Session):
    return business_module_repository.get_business_modules(db)
