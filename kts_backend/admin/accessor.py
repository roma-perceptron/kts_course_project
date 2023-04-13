from sqlalchemy import select

from kts_backend.admin.models import AdminModel
from kts_backend.store.base_accessor import BaseAccessor


class AdminAccessor(BaseAccessor):
    async def get_admin(self, email: str, password: str):
        query = (
            select(AdminModel.id, AdminModel.email, AdminModel.password)
            .where(AdminModel.email == email)
            .where(AdminModel.password == password)
        )
        admin = await self.execute_query(query)
        return admin

    async def set_admin(self, email: str, password: str):
        admin = await self.get_or_create(
            AdminModel,
            email=email,
            password=password
        )
        return admin
