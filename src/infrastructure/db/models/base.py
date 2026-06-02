from sqlalchemy.orm import DeclarativeBase


## Создает объект MetaData под капотом
## repr - метод для читаемого отображения


class Base(DeclarativeBase):
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__dict__})"
