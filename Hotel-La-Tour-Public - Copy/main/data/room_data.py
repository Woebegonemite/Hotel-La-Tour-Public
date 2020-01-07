import sqlalchemy as sa
from main.data.model_base import SqlAlchemyBase
from sqlalchemy import orm

# Contains all data about each of the rooms that the hotel provides, this
# is executed when data about each of the rooms needs to be returned. There
# is also a relationship that returns all of the bookings that customers
# have made for each room
class Room_Data(SqlAlchemyBase):
    __tablename__ = 'Room_Datum'
    room_id = sa.Column(sa.Integer, primary_key=True)
    room_name = sa.Column(sa.String)
    description = sa.Column(sa.String)
    room_bookings = orm.relation("Room_Booking", backref="room_data")
