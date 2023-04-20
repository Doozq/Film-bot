import sqlalchemy
from .db_session import SqlAlchemyBase


class Film(SqlAlchemyBase):
    __tablename__ = 'films'

    code = sqlalchemy.Column(sqlalchemy.Integer,
                             primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    url = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    img = sqlalchemy.Column(sqlalchemy.BLOB)
