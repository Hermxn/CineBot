from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    telegram_id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str]
    last_name: Mapped[str | None]
    username: Mapped[str | None]

    def __repr__(self) -> str:
        return f'User(id={self.id!r}, name={self.first_name!r}, fullname={self.last_name!r})'


class Follows(Base):
    __tablename__ = 'follows'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_telegram_id: Mapped[int] = mapped_column(ForeignKey('users.telegram_id'))
    movie_id: Mapped[int]
    movie_name: Mapped[str]

    def __repr__(self) -> str:
        return f'User(id={self.id!r}, name={self.movie_id!r}, fullname={self.movie_name!r})'
