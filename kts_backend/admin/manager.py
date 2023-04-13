import typing

from kts_backend.admin.accessor import AdminAccessor
from kts_backend.utils import hash_it

if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application


class AdminManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.accessor: AdminAccessor = AdminAccessor(app)
        #
        self.app.on_startup.append(self.create_initial_admin)

    async def create_initial_admin(self, *args):
        admin, created = await self.accessor.set_admin(
            email=self.app.config.admin.email,
            password=hash_it(self.app.config.admin.password)
        )
        if created:
            print('Initial admin account created!')
        elif admin:
            print('Admin account already done')