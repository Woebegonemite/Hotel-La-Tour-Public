import sqlalchemy as sa
from sqlalchemy import orm
from main.data.model_base import SqlAlchemyBase

# A simple table that contains whether a user has subscribed to the hotel's emailing
# system
class Subscription(SqlAlchemyBase):
    __tablename__ = 'Subscriptions'
    subscription_id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    customer_id = sa.Column(sa.Integer, sa.ForeignKey("Customer.id"))
    customer = orm.relation("Customer", backref="is_subscribed")