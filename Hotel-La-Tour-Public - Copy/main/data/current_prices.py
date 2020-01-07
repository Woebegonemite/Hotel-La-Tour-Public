import sqlalchemy as sa
import datetime, random
from main.data.model_base import SqlAlchemyBase

# Contains the current prices for each type of room that the hotel provides
# This is used to determine the total transaction of a user booking
class Current_Price(SqlAlchemyBase):
    __tablename__ = 'Current_Prices'
    date = sa.Column(sa.Date, primary_key=True, default=datetime.date.today())
    standard_room_price = sa.Column(sa.Integer, default=70+random.randint(1, 30), nullable=False)
    executive_price = sa.Column(sa.Integer, default=100+random.randint(1, 30), nullable=False)
    suite_one_price = sa.Column(sa.Integer, default=120+random.randint(1, 30), nullable=False)
    suite_two_price = sa.Column(sa.Integer, default=150+random.randint(1, 30), nullable=False)
