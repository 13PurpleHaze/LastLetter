from fastapi import FastAPI
from sqladmin import ModelView
from infrastructure.db.models import User, Capsule, Role, Content
from sqladmin import Admin

from infrastructure.engine import session_maker


class UserAdmin(ModelView, model=User):  # type: ignore[call-arg]
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"
    category_icon = "fa-solid fa-user"
    column_list = [
        User.id,
        User.first_name,
        User.email,
        User.email_verified,
        User.is_deceased,
        User.date_of_birth,
        User.verificator,
        User.roles,
        User.parents,
        User.children,
    ]
    form_excluded_columns = [User.capsules]


class RoleAdmin(ModelView, model=Role):  # type: ignore[call-arg]
    name = "Role"
    icon = "fa-solid fa-users"
    column_list = [
        Role.id,
        Role.slug,
        Role.title,
    ]


class CapsuleAdmin(ModelView, model=Capsule):  # type: ignore[call-arg]
    name = "Capsule"
    icon = "fa-solid fa-box"
    column_list = [Capsule.id, Capsule.title, Capsule.send_at, Capsule.creator]
    form_excluded_columns = [Capsule.contents]


class ContentAdmin(ModelView, model=Content):  # type: ignore[call-arg]
    name = "Content"
    icon = "fa-solid fa-image"
    column_list = [
        Content.id,
        Content.object_key,
        Content.content_type,
        Content.capsule,
    ]


def setup_admin(app: FastAPI):
    admin = Admin(app=app, session_maker=session_maker)

    admin.add_view(UserAdmin)
    admin.add_view(RoleAdmin)
    admin.add_view(CapsuleAdmin)
    admin.add_view(ContentAdmin)
