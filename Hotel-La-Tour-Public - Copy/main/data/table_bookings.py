import sqlalchemy as sa
from main.data.model_base import SqlAlchemyBase

# Holds data related to table bookings at the hotel's restaurant. This has not been
# fully implemented in the actual website but is still valid
class Table_Booking(SqlAlchemyBase):
    __tablename__ = 'Table_Bookings'
    transaction_id = sa.Column(sa.Integer, sa.ForeignKey("Transactions.transaction_id"), primary_key=True)
    start_time = sa.Column(sa.DateTime, nullable=False)
    table_type = sa.Column(sa.Integer)