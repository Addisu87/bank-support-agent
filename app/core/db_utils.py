# # app/core/db_utils.py
# from contextlib import asynccontextmanager
# from sqlalchemy import select
# from app.db.session import AsyncSessionLocal
# from app.db.schema import User


# @asynccontextmanager
# async def get_user_db(email: str):
#     """
#     Async context manager that yields (db, user)
#     based on the provided email.
#     """
#     async with AsyncSessionLocal() as db:
#         result = await db.execute(select(User).filter_by(email=email))
#         user = result.scalar_one_or_none()
#         yield db, user
