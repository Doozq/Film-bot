import sqlalchemy
from .db_session import SqlAlchemyBase


class Chanel(SqlAlchemyBase):
    __tablename__ = 'chanels'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    url = sqlalchemy.Column(sqlalchemy.String, nullable=True)
