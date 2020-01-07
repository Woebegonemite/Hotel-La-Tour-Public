import sqlalchemy as sa
from main.data.model_base import SqlAlchemyBase

# Contains all the customers bookings, and all the data needed for that booking, like the
# arrival and end date. Each booking is related to one transaction, and one transaction can have
# many room bookings, as a customer can book 6 rooms in one transaction. The room_id references
# the type of room that the customer has booked (eg. standard room), this  is used to establish
# a relationship so that information about the specific rooms can easily be referenced
class Room_Booking(SqlAlchemyBase):
    __tablename__ = 'Room_Bookings'
    booking_id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    transaction_id = sa.Column(sa.Integer, sa.ForeignKey("Transactions.transaction_id"))
    start_date = sa.Column(sa.Date, nullable=False)
    end_date = sa.Column(sa.Date, nullable=False)
    room_id = sa.Column(sa.Integer, sa.ForeignKey("Room_Datum.room_id"))
