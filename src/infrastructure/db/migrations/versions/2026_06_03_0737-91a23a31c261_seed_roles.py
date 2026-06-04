"""seed roles

Revision ID: 91a23a31c261
Revises: cf12dd70e5a2
Create Date: 2026-06-03 07:37:39.370956

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from constants import RoleId, RoleSlug

# revision identifiers, used by Alembic.
revision: str = "91a23a31c261"
down_revision: Union[str, Sequence[str], None] = "cf12dd70e5a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    roles = sa.table(
        "roles",
        sa.column("role_id", sa.Integer),
        sa.column("slug", sa.String),
        sa.column("title", sa.String),
    )
    op.bulk_insert(
        roles,
        [
            {
                "id": RoleId.ADMIN,
                "slug": RoleSlug.ADMIN,
                "title": "Администратор",
            },
            {
                "id": RoleId.PARENT,
                "slug": RoleSlug.PARENT,
                "title": "Родитель",
            },
            {
                "id": RoleId.CHILD,
                "slug": RoleSlug.CHILD,
                "title": "Ребенок",
            },
            {
                "id": RoleId.VERIFIER,
                "slug": RoleSlug.VERIFIER,
                "title": "Верификатор",
            },
        ],
    )
    pass


def downgrade() -> None:
    op.execute(
        f"DELETE FROM roles WHERE role_id IN ("
        f"{RoleId.ADMIN}, {RoleId.PARENT}, {RoleId.CHILD}, {RoleId.VERIFIER}"
        f")"
    )
    pass
