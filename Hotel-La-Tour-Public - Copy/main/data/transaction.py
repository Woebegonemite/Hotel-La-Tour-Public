import sqlalchemy as sa
from main.data.model_base import SqlAlchemyBase
from sqlalchemy import orm

# Holds all transactional data referring to when a user books a room or table
# with the hotel. Each transaction can have many rooms or tables as a transaction
# can involve many bookings. The cost contains the total price of all the rooms
# or tables that the customer booked, this is determined when the transaction is
# implemented and must be greater than 0. Customer_Id relates to a specific customer
# on the website and a customer can have many transactions, which can have many bookings.
# The receipt is determined after the transaction has taken place, and is a hash of the
# transaction_id, meaning that all transactions will have a unique receipt. This is used
# for refunding a transaction that has taken place
class Transaction(SqlAlchemyBase):
    __tablename__ = 'Transactions'
    transaction_id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    booked_rooms = orm.relation("Room_Booking", backref="transaction")
    booked_tables = orm.relation("Table_Booking", backref="transaction")
    cost = sa.Column(sa.Integer, sa.CheckConstraint("cost > 0"), nullable=False)
    customer_id = sa.Column(sa.Integer, sa.ForeignKey("Customer.id"))
    receipt = sa.Column(sa.String)
