import sqlalchemy as sa
from sqlalchemy import orm
from datetime import datetime
from main.data.model_base import SqlAlchemyBase

# A many-to-many self referencing table that contains all the customer connections,
# a connection means that the customer is friends with another customer. The pending
# field is used for determine whether the relationship is fully established (both
# customers agree to be 'friends') or if one customer has sent a request to another
# customer and is waiting for that other customer to accept. If pending is true, then
# the connection is not fully established
Customer_Connection = sa.Table(
    "Customer_Connection",
    SqlAlchemyBase.metadata,
    sa.Column("connection_id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("customer_primary_id", sa.Integer, sa.ForeignKey("Customer.id")),
    sa.Column("customer_secondary_id",sa.Integer, sa.ForeignKey("Customer.id")),
    sa.Column("pending", sa.Boolean, default=True),
    sa.Column("date_created", sa.Date, default=datetime.now()),
)

# Contains all data related to a customer. This includes all the information about the
# customer (eg. title, address, ext...), as well as relationships to all their bookings
# and connected friends
class Customer(SqlAlchemyBase):
    __tablename__ = 'Customer'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    first_name = sa.Column(sa.String, nullable=False)
    last_name = sa.Column(sa.String, nullable=False)
    title = sa.Column(sa.String)
    email = sa.Column(sa.String, nullable=False, index=True)
    password = sa.Column(sa.String, nullable=False, index=True)
    dob = sa.Column(sa.Date)
    tel_number = sa.Column(sa.String)
    country = sa.Column(sa.String)
    postal_code = sa.Column(sa.String)
    address = sa.Column(sa.String)
    creation_date = sa.Column(sa.DateTime, default=datetime.now)
    bookings = orm.relation("Transaction", backref="customer")
    friends = orm.relation("Customer", secondary="Customer_Connection",
                           primaryjoin=(id == Customer_Connection.c.customer_primary_id),
                           secondaryjoin=id == Customer_Connection.c.customer_secondary_id)
