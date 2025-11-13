from sqlalchemy.orm import Session
from app.dtos.business_module_dto import BusinessModuleDTO
from app.repositories import business_module_repository


def get_business_module(db: Session):
    return business_module_repository.get_business_modules(db)
