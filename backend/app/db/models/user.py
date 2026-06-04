"""用户 ORM 模型。"""

from sqlalchemy import String, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import BaseModel


class User(BaseModel):
    """系统用户模型。"""

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    avatar: Mapped[str] = mapped_column(Text, nullable=True)  # base64 或 URL
    display_name: Mapped[str] = mapped_column(String(100), nullable=True)

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.email}) role={self.role}>"
