# This file is used for including all the ORM classes that will
# Be used in the database, this is mainly used so that all classes
# Can easily be included. I understand that I only have one ORM class
# For this project but it is still good practice to follow this
# Methodology

from main.data.avaliable_rooms import Avaliable_Room
from main.data.room_data import Room_Data
from main.data.customer import Customer
from main.data.customer import Customer_Connection
from main.data.current_prices import Current_Price
from main.data.subscription import Subscription
from main.data.transaction import Transaction
from main.data.room_bookings import Room_Booking
from main.data.table_bookings import Table_Booking