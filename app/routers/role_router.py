import logging
from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from requests import Session
from app.database import get_db
from app.dtos.role_dto import UserRoleCreateDTO
from app.services import user_service
from app.services.auth_service import AuthService


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/role", tags=["Role"])


# @router.post("/")
# async def create_user_role(
#     dto: UserRoleCreateDTO,
#     db: Session = Depends(get_db),
# ):
#     # 1. Find user by email
#     user = user_service.get_user_by_email(db, dto.email)
#     if not user:
#         raise HTTPException(
#             status_code=404, detail={"msg": "User not found", "type": "user not found"}
#         )

#     # 2. Check if role_id exists (for org)
#     if data.scope_type == "org":
#         role = await session.execute(select(Role).where(Role.id == data.role_id))
#         if role.scalar_one_or_none() is None:
#             raise HTTPException(status_code=404, detail="Role not found")

#     # 3. Insert into user_roles
#     stmt = insert(user_roles).values(
#         user_id=user.id,
#         scope_type=data.scope_type,
#         scope_id=data.scope_id,
#         role_id=data.role_id,
#     )

#     try:
#         await session.execute(stmt)
#         await session.commit()

#     except Exception as e:
#         await session.rollback()
#         raise HTTPException(status_code=400, detail=str(e))

#     return {"message": "User role created successfully"}
