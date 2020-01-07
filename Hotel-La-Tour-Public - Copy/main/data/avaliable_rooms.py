import sqlalchemy as sa
import datetime, random
from main.data.model_base import SqlAlchemyBase

# Contains how many rooms are avaliable for each room type for each specific date
class Avaliable_Room(SqlAlchemyBase):
    __tablename__ = 'Avaliable_Rooms'
    date = sa.Column(sa.Date, primary_key=True, default=datetime.date.today())
    standard_room_availability = sa.Column(sa.Integer, sa.CheckConstraint("standard_room_availability >= 0"), default=80, nullable=False)
    executive_room_availability = sa.Column(sa.Integer, sa.CheckConstraint("executive_room_availability >= 0"), default=50, nullable=False)
    suite_one_availability = sa.Column(sa.Integer, sa.CheckConstraint("suite_one_availability >= 0"), default=10, nullable=False)
    suite_two_availability = sa.Column(sa.Integer, sa.CheckConstraint("suite_two_availability >= 0"), default=5, nullable=False)
