import hashlib, flask, datetime, logging, random
from flask import Response
from passlib.handlers.sha2_crypt import sha512_crypt as crypto
import main.data.db_session as db
from main.data.room_bookings import Room_Booking
from main.data.room_data import Room_Data
from main.data.avaliable_rooms import Avaliable_Room
from main.data.current_prices import Current_Price
from main.data.customer import Customer, Customer_Connection
from main.data.subscription import Subscription
from main.data.table_bookings import Table_Booking
from main.data.transaction import Transaction
from sqlalchemy import func
from sqlalchemy.engine.result import ResultProxy
from collections import defaultdict

# This file is the most important script that is used in the website.
# All functions that require access to the database are executed via
# this script, the reason for that is that all database transactions can
# be backtracked to this file and ultimately this makes the data transfer
# between the website views and the database more encapsulated and reduces
# repeating copying the same code across multiple views. Most of the
# cookie functions are also executed in this file. This is referenced in the
# view files as 'cf'


# Logging has been individually set for this file, as transactions in the database
# are important and must be recorded

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler("../logs/database_trans_logs.log")
file_handler.setFormatter(logging.Formatter("%(asctime)s:%(name)s:%(message)s"))

logger.addHandler(file_handler)

# Hashes data passed to the function, this used for hashing user passwords
def hash_text(text: str) -> str:
    return crypto.encrypt(text, rounds=171204)


# Verifies that the hashed password from the database matches the user's plain text password input
def verify_hash(hashed_text: str, plain_text: str) -> bool:
    return crypto.verify(plain_text, hashed_text)


# Creates a sha512 hash that is used for creating secure account cookies and hashing to
# produce transaction receipts
def __hash_text(text: str) -> str:
    text = 'salty__' + text + '__text'
    return hashlib.sha512(text.encode('utf-8')).hexdigest()


# Sets a valid account cookie consisting of the user id and a verification hash, the hash must be valid
# for the user to have access to the website on their account. This avoids users manipulating their cookie
# and gaining access to someone else's account; each cookie must have a valid hash, and that can only be
# calculated from this file
def set_auth(response: Response, user_id: int):
    hash_val = __hash_text(str(user_id))
    val = "{}:{}".format(user_id, hash_val)  # Sets the user's id as well as hash value
    response.set_cookie("hlt_account_cookie", val, max_age=datetime.timedelta(days=30))  # Sets cookie


# Destroys the user's account cookie, this is mainly utilised when the user wants to log out
def destroy_cookie(response: Response):
    response.set_cookie("hlt_account_cookie", "", expires=0)  # Sets cookie to expire immediately


# Validates that the user has a valid cookie, if so, then the user can access their account
def check_valid_account_cookie(request: flask.request):
    if "hlt_account_cookie" not in request.cookies:  # Cookie does not exist
        return None

    val = request.cookies["hlt_account_cookie"]
    split_list = val.split(":")
    if len(split_list) != 2:
        logger.info(f"IP:{request.access_route} contains invalid cookie")
        return None

    user_id = split_list[0]  # User Id is returned
    hash_val = split_list[1]  # Hash is returned
    hash_val_check = __hash_text(user_id)  # Hashed is checked to make sure the cookie is valid (ensures someone cannot
    if hash_val != hash_val_check:  # access the user account unless they have logged in successfully)
        logger.info(f"IP:{request.access_route} has invalid cookie hash")
        return None

    try:
        user_id = int(user_id)  # Attempts to convert ID to int
    except ValueError:
        response: Response = flask.redirect("/login")  # If there is an error, then the cookie is invalid and is destroyed
        logger.info(f"IP:{request.access_route} contains invalid cookie")
        destroy_cookie(response)
    else:
        return user_id # User_id is returned and the customer can successful access their account data


# Utilised when creating a new customer on the database. This adds all the data entered by the user at the register page,
# And if the user agrees to subscribe to the hotel emails, then they are added to the subscribed table
def create_customer(title, password, first_name, last_name, email, tel_number, dob, postcode, address, country, city, is_subbed):
    session = db.create_session()
    new_customer: Customer = Customer()
    new_customer.title = title.lower()
    new_customer.password = hash_text(password)
    new_customer.first_name = first_name.lower()
    new_customer.last_name = last_name.lower()
    new_customer.email = email
    new_customer.tel_number = tel_number
    new_customer.dob = dob
    new_customer.postal_code = postcode
    new_customer.address = address.lower()
    new_customer.country = country.lower()
    new_customer.city = city.lower()
    session.add(new_customer)

    logger.info(f"New Customer {new_customer.id} added")

    if is_subbed:
        session.flush()
        new_subscription: Subscription = Subscription()
        new_subscription.customer_id = new_customer.id
        session.add(new_subscription)
        logger.info(f"Customer {new_customer.id} added to subscription table")

    session.commit()
    return new_customer


# Checks that the user has entered in a valid email by searching the database and returning
# whether an email exists or not. This is mainly used to check that the user is not registering
# with an existing email
def check_if_email_exists(email: str) -> bool:
    if not email:
        return False
    session = db.create_session()
    logger.info(f"Checking if user:{email} exists in database")
    returned_user = session.query(Customer).filter(Customer.email == email).first()  # User of that email is searched
    session.close()
    if returned_user is None:
        logger.info(f"True: {email} does not exist in database")
        return False
    else:
        logger.info(f"False: {email} does exist in database")
        return True


# Checks if a user of the inputted email exists and has the correct password (the user input matches
# the hashed password stored in the database)
def check_user_is_in_database_and_password_valid(email: str, password: str):
    if not email or not password:
        return None

    session = db.create_session()
    returned_user = session.query(Customer).filter(Customer.email == email).first()

    logger.info(f"Checking if:{email} has correct password")

    if not returned_user:
        logger.info(f"False: {email} does not exist")
        return False

    if not verify_hash(returned_user.password, password):  # Password does not match encrypted password
        logger.info(f"False: {email} did not enter correct password")
        return False

    session.close()
    logger.info(f"True: {email} did enter correct password")
    return returned_user


# Checks that the input that is submitted by the user is valid (has correct length, doesn't contain
# Malicious characters that could be used for practices such as an SQL injection, and the data actually exists).
# This is used when the user is registering
def check_if_input_error(input: str) -> str:
    bad_chars = "!\"#$%&'()*+-./:;<=>?@[\\]^_`{|}~"
    logger.info(f"Checking if: {input} are valid")

    if not input:
        logger.info(f"False: {input} is not correctly inputted")
        return "Input Error: All fields must be entered"

    elif len(input) <= 3 or len(input) > 40:
        logger.info(f"False: {input} are not of correct size")
        return f"Input Error: {input} not of correct size (both must be greater than 7 and smaller than 20)"

    for bad_character in bad_chars:
        if bad_character in input:
            logger.info(f"False: {input} contains bad character: {bad_character}")
            return f"Input Error: {input} cannot contain: " + bad_character


# Simply returns the user with matching ID. Mainly used when a user has a verified cookie and needs access to
# customer details
def return_customer(account_id):
    session = db.create_session()
    returned_user: Customer = session.query(Customer).filter(Customer.id == account_id).first()
    if returned_user:
        logger.info(f"Attempting to return user: {returned_user.first_name}")
    else:
        logger.info(f"Failed to return user with ID: {account_id}")
    return returned_user


# Returns a customer with a specific email
def return_customer_with_email(add_email):
    session = db.create_session()
    returned_user: Customer = session.query(Customer).filter(Customer.email == add_email).first()
    if returned_user:
        logger.info(f"Attempting to return user: {returned_user.first_name}")
    else:
        logger.info(f"Failed to return user with ID: {add_email}")
    return returned_user


# Creates a connection between two users. Unfortunately, I was not able to figure out a method of creating a
# many to many self-referencing data class with out creating errors and problems, therefore the connection table
# was implemented as a table. Therefore access to the table had to be executed as raw SQL inputs, this is a shame
# as it is less effective and harder to execute efficiently than using object related mapping.
# Customer_active refers to the id of the customer who is establishing a connection with another customer, and
# customer_submissive is the id of the customer who will receive this connection. The pending value is set to
# false as the connection has not been fully established; this only changes once a the customer receiving the
# request accepts the connection. The function first checks that a connection does not already exist before creating
# a new connection
def create_connection(customer_active: int, customer_submissive: int):
    logger.info(f"Creating a new connection between customers: {customer_active} and {customer_submissive}")
    session = db.create_session()
    existing_connection: ResultProxy = session.execute("SELECT * FROM Customer_Connection WHERE customer_primary_id ==" +
                                                    str(customer_active) + " AND customer_secondary_id ==" + str(customer_submissive))
    returned_results = []
    for row in existing_connection:
        returned_results.append(row)

    if returned_results:
        logger.info(f"Customers: {customer_active} and {customer_submissive} already have an existing connection; "
                    f"thus a new connection cannot be established")
        session.close()
        return False

    session.execute("INSERT INTO Customer_Connection(customer_primary_id,customer_secondary_id,pending,date_created) "
                    "VALUES (" + str(customer_active) + ", " + str(customer_submissive) + ", 1, '"+
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "');")
    logger.info(f"Connection between: {customer_active} and {customer_submissive} is successfully established")
    session.commit()
    session.close()
    return True


# Updates an existing connection from pending to complete (meaning that data is now passed between the two users)- this
# Is done by setting the pending field to False. This is referenced when a customer accepts a connection request
def update_connection(customer_active: int, customer_submissive: int):
    logger.info(f"Establishing a new connection between customers: {customer_active} and {customer_submissive}")
    session = db.create_session()
    existing_connection: ResultProxy = session.execute("SELECT * FROM Customer_Connection WHERE customer_primary_id == "+
                                                       str(customer_active)+" AND customer_secondary_id == "+str(customer_submissive)+
                                                       " AND Pending=1")

    returned_results = []
    for row in existing_connection:
        returned_results.append(row)

    if not returned_results:
        logger.info(f"Customers: {customer_active} and {customer_submissive} cannot update a connection as no connection exists")
        session.close()
        return False

    session.execute("UPDATE Customer_Connection SET pending = 0 WHERE customer_primary_id =="+
                            str(customer_active)+" AND customer_secondary_id =="+str(customer_submissive))
    logger.info(f"Connection fully established between: {customer_active} and {customer_submissive}")
    session.commit()
    session.close()
    return True


# Returns all pending connections for a specific customer. This is where a connection exists but the connection
# is still pending (the customer with the secondary_id has not accepted the friend request)
def return_pending_connections(customer_submissive: int):
    logger.info(f"Returning all pending connections for customer: {customer_submissive}")
    session = db.create_session()
    pending_connections = session.execute("SELECT * FROM Customer_Connection WHERE customer_secondary_id =="+
                                          str(customer_submissive)+" AND Pending == 1")

    user_primary_id = []
    for row in pending_connections:
        user_primary_id.append(row[1])

    pending_friends = []
    for friend_id in user_primary_id:
        logger.info(f"Customer: {customer_submissive} has a pending connection: {friend_id}")
        pending_friends.append(return_customer(friend_id))

    session.close()
    return pending_friends


# Similiar to the return pending connections function, this function deals with returning all the connections
# that are fully established; where both customers have agreed to have a shared connection (pending is false)
def return_established_connections(customer_id):
    logger.info(f"Returning all established connections for customer: {customer_id}")
    session = db.create_session()
    connections = session.execute("SELECT * FROM Customer_Connection WHERE customer_secondary_id =="+
                                          str(customer_id)+" AND Pending == 0 OR customer_primary_id =="+
                                          str(customer_id))

    friend_row = []
    for row in connections:
        if row[1] != customer_id:
            friend_row.append(row[1])
        elif row[2] != customer_id:
            friend_row.append(row[2])

    friends = []
    for friend_id in friend_row:
        logger.info(f"Customer: {customer_id} has an established connection with: {friend_id}")
        friends.append(return_customer(friend_id))

    return friends


# Deletes a connection, this is referenced when a customer declines a connection request. In this instance, the pending
# connection is deleted
def delete_connection(customer_active: int, customer_submissive: int):
    session = db.create_session()

    if customer_active == customer_submissive:
        return None

    session.execute("DELETE FROM Customer_Connection WHERE (customer_secondary_id = "+str(customer_submissive)+
                    " AND customer_primary_id = "+str(customer_active)+") OR (customer_secondary_id = "
                    +str(customer_active)+" AND customer_primary_id = "+str(customer_active)+")")

    logger.info(f"Connection between {customer_submissive} and {customer_active} removed")

    session.commit()
    session.close()


# Checks if any connection exists between customers
def check_connection_already_pending_or_exists(customer_active: int, customer_submissive: int):
    logger.info(f"Checking connection between {customer_submissive} and {customer_active}")

    if customer_active == customer_submissive:
        return None

    session = db.create_session()
    existing_connection: ResultProxy = session.execute("SELECT * FROM Customer_Connection WHERE customer_primary_id =="+
                                          str(customer_active)+" AND customer_secondary_id =="+str(customer_submissive))

    returned_results = []
    for row in existing_connection:
        returned_results.append(row)

    if not returned_results:
        logger.info(f"Connection between {customer_submissive} and {customer_active} does not exist")
        session.close()
        return False

    logger.info(f"Connection between {customer_submissive} and {customer_active} does exist")
    session.close()
    return True

# Changes the user's password
def change_user_password(customer_id, password):
    session = db.create_session()
    customer = session.query(Customer).filter(Customer.id == customer_id).first()
    print(customer)
    if not customer:
        return False
    customer.password = hash_text(password)
    logger.info(f"User {customer_id} changed password")
    session.commit()
    session.close()


# This function is only executed by myself when resetting the database, mainly for testing or
# removing erroneous data. If the actual website was implemented properly then this function
# would be removed as it could be used maliciously, but for the purpose of this project it
# has been implemented as such
def delete_all_from_database(devs):
    session = db.create_session()
    users = session.query(Customer).all()
    connections = session.query(Room_Booking).all()
    subscriptions = session.query(Subscription).all()
    tables = session.query(Table_Booking).all()
    transactions = session.query(Transaction).all()
    room_date = session.query(Room_Data).all()
    room_prices = session.query(Current_Price).all()
    available_rooms = session.query(Avaliable_Room).all()

    logger.info("DELETING ALL FROM DATABASE")
    for data in room_date:
        session.delete(data)
    for price in room_prices:
        session.delete(price)
    for current_available in available_rooms:
        session.delete(current_available)
    for user in users:
        if user.email not in devs:
            session.delete(user) # Developer users are not deleted to save re-registering
    for connection in connections:
        session.delete(connection)
    for subscription in subscriptions:
        session.delete(subscription)
    for table in tables:
        session.delete(table)
    for transaction in transactions:
        session.delete(transaction)

    session.commit()
    logger.info("DATABASE NOW EMPTY")
    session.close()


# This function is similar to the 'delete all' function and is only used for development;
# it simply: populates the room_data field with all the room information; resets all the
# available rooms to the amount of rooms in the hotel; and creates pseudo-random fluctuating
# prices for each of the rooms, to mimic what the prices would really be implemented when the
# hotel is properly developed. This, like the 'delete all' function have only been implemented
# for development
def update_database():
    session = db.create_session()
    room_data = session.query(Room_Data).all()

    room_names = ["Standard Room", "Executive Room", "Suite One", "Suite Two"]

    description = [
        "Regardless of who you are, the Standard Room will always be a go to pick for comfort and affordability,\
        Each room is equipped with a 38\" LED flat screen TV, a modern bathroom with a dual control monsoon shower,\
        laptop safe, iron & ironing board, tea & coffee making facilities as well as air conditioning and complimentary WiFi:\
        Dual control monsoon shower with toiletries,\
        Tea/Coffee making facilities,\
        Complimentary bottle of water,\
        24 hour Room Service,\
        42” LED flat screen TV with live record,\
        Large desk area with work lamp,\
        Dual control monsoon shower with toiletries,\
        King size bed with luxury topper,\
        Iron & Ironing Boards\
        ",

        "The most classy room of all the options offered by the hotel. Relax in the King size bed or stylish chaise lounge\
         and enjoy a refreshing shower in the dual control monsoon shower.All rooms feature a 42″ LED flat screen TV, a laptop safe,\
        tea & coffee making facilities, iron & ironing board as well as air conditioning and 24 hour room service.:\
        Dual control monsoon shower with toiletries,\
        Tea/Coffee making facilities,\
        Complimentary bottle of water,\
        24 hour Room Service,\
        42” LED flat screen TV with live record,\
        Large desk area with work lamp,\
        Dual control monsoon shower with toiletries,\
        King size bed with luxury topper,\
        Iron & Ironing Boards",

        "Each of the Suite One rooms provide ample space to relax and unwind. If you are travelling on \
        business there is plenty of space to work with a large desk area; or if you are enjoying a night \
        in Birmingham city, you can get ready in comfort enjoying a complimentary bottle of wine & chocolates.\
        These rooms are designed with relaxation in mind, featuring a King size bed, comfortable \
        armchair, a large shower and extra-deep bath with a built in TV above.: \
        42″ LED flat screen TV and Nespresso coffee machine.\
        Laptop safe,\
        Nespresso Coffee Machine,\
        Complimentary bottle of wine and chocolates,\
        Bathroom with TV,\
        Extra-deep bath,\
        Anti-steam mirror,\
        Large walk-in shower,\
        Bathrobe and Slippers,\
        Luxury toiletries",

        "Suite two rooms at Hotel La Tour offer the best in luxury. Relax in the separate lounge area with large sofa and 42” LED Flat screen TV or unwind in the \
        extra-deep bath with in-built TV. Each suite is also equipped with large walk-in monsoon shower, audio speakers and Nespresso coffee machine.\
        Our Suites are extra spacious with their own separate lounge area, king size bed and complimentary bottle of wine and chocolates.:\
        King size bed with luxury topper,\
        Separate lounge area with large sofa,\
        Climate control,\
        Air-conditioning,\
        Audio speakers,\
        King or Twin bed available,\
        Dual control monsoon shower with toiletries,\
        Separate lounge area with large sofaat screen TV with live record"
    ]

    if not room_data:
        for i in range(4):
            room_info = Room_Data()
            room_info.room_id = i
            room_info.room_name = room_names[i]
            room_info.description = description[i]
            session.add(room_info) # Room information is added

    logger.info("Room information is added")
    current_date = datetime.date.today()
    for i in range(30): # Random prices are added for the next thirty days
        search_date = current_date + datetime.timedelta(days=i)
        query_cost = session.query(Current_Price).filter(Current_Price.date == search_date).first()
        if not query_cost:
            new_cost = Current_Price()
            new_cost.date = search_date
            new_cost.standard_room_price = 70 + random.randint(1, 30)
            new_cost.executive_price = 100 + random.randint(1, 30)
            new_cost.suite_one_price = 120 + random.randint(1, 30)
            new_cost.suite_two_price = 150 + random.randint(1, 30)
            session.add(new_cost)
            logger.info(f"Random room costs for day {current_date} set")
        query_avaliable_rooms = session.query(Avaliable_Room).filter(Avaliable_Room.date == search_date).first()
        if not query_avaliable_rooms:
            new_available_room = Avaliable_Room()
            new_available_room.date = search_date
            session.add(new_available_room)
            logger.info(f"Avaliable rooms for day {current_date} set to max values")
        session.commit()
    session.close()


# Returns a transaction based on the receipt entered. This is utilised for when a customer
# wants to delete a transaction
def return_transaction_by_receipt(receipt):
    session = db.create_session()
    transaction = session.query(Transaction).filter(Transaction.receipt == receipt).first()
    if not transaction:
        return None, session
    logger.info(f"Returning {transaction} with receipt: {receipt}")
    return transaction, session


# Returns a room data object based on the room id. This is mainly for when
# the room information needs to be displayed by the website
def return_room_with_id(room_id):
    session = db.create_session()
    room = session.query(Room_Data).filter(Room_Data.room_id == room_id).first()
    if not room:
        return None
    logger.info(f"Returning room: {room.room_id}")
    session.close()
    return room


# Returns all available rooms between two dates. This is used mainly for when the user queries available rooms
# while booking
def return_available_rooms_inbetween_dates(start_date: str, end_date: str):
    session = db.create_session()
    start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    if end_date-start_date > datetime.timedelta(weeks=2): # Makes sure that user cannot create a booking longer than two weeks
        return None
    available_rooms = session.query(Avaliable_Room).filter(Avaliable_Room.date.between(start_date, end_date)).all()
    logger.info(f"Returning avaliable rooms between: {start_date} and {end_date}")
    return available_rooms


# Returns the current prices of all rooms between two dates. Mainly used for when the user queries avaiaable rooms
def return_room_costs(start_date: str, end_date: str):
    session = db.create_session()
    start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    if end_date-start_date > datetime.timedelta(weeks=2):
        return None
    current_prices = session.query(Current_Price).filter(Current_Price.date.between(start_date, end_date)).all()
    logger.info(f"Returning room costs between: {start_date} and {end_date}")
    return current_prices


# Creates a cookie that refers to a specific booking in the user's basket. This is used for creating all the cookies that
# hold the information related to the customer's current booking session
def create_basket_cookie(num: int, room_name: int, start_date: datetime.date, end_date: datetime.date, cost:int, response: flask.Response):
    data = f"{room_name}:{start_date}:{end_date}:{cost}"
    logger.info(f"Creating new booking cookie: {room_name}:{start_date}:{end_date}:{cost}")
    response.set_cookie("basket_cookie:"+str(num), data.replace("\"",""), max_age=datetime.timedelta(hours=1))  # Sets cookie


# This is a very important function for the website, and handles the user creating a transaction and booking the rooms.
# This works as follows:
# - All bookings are returned from the user's basket cookies that are stored
# - A new transaction is created and the cost set to the total cost of the booking
# - The receipt is created as a hash of the new transaction id
# - Each room is added to the newly created transaction
# - For each room duration, the room availability for that specific room is decreased by one (as the room is now booked)
# - The transaction is added and the receipt is returned to be displayed to the user
def create_transaction_and_book_rooms(customer, request: flask.Request):
    if not customer:
        return None
    logger.info(f"Creating new transaction for customer: {customer.id}")
    session = db.create_session()
    new_Transaction = Transaction()
    new_Transaction.customer_id = customer.id
    if not check_rooms(request):
        return False

    total_cost, rooms = return_rooms_from_cookie(request)

    new_Transaction.cost = total_cost
    session.add(new_Transaction)
    session.flush()
    new_Transaction.receipt = __hash_text(str(new_Transaction.transaction_id))
    logger.info(f"New transaction: {new_Transaction.transaction_id}- total cost: {new_Transaction.cost}- receipt: {new_Transaction.receipt}")
    for room in rooms:
        room.transaction_id = new_Transaction.transaction_id
        room.start_date = datetime.datetime.strptime(room.start_date, "%Y-%m-%d").date()
        room.end_date = datetime.datetime.strptime(room.end_date, "%Y-%m-%d").date()
        session.add(room) # Room is booked
        session.flush()
        logger.info(f"Room booked: {room.room_id} for new transaction: {new_Transaction.transaction_id}")
        start_date = room.start_date
        while start_date <= room.end_date: # For each day a room is booked the availability is decreased
            if room.room_id == 0:
                avaliable_room = session.query(Avaliable_Room).filter(Avaliable_Room.date == start_date).first()
                avaliable_room.standard_room_availability -= 1
            elif room.room_id == 1:
                avaliable_room = session.query(Avaliable_Room).filter(Avaliable_Room.date == start_date).first()
                avaliable_room.executive_room_availability -= 1
            elif room.room_id == 2:
                avaliable_room = session.query(Avaliable_Room).filter(Avaliable_Room.date == start_date).first()
                avaliable_room.suite_one_availability -= 1
            elif room.room_id == 3:
                avaliable_room = session.query(Avaliable_Room).filter(Avaliable_Room.date == start_date).first()
                avaliable_room.suite_two_availability -= 1
            else:
                return False
            start_date += datetime.timedelta(days=1)
    session.commit()
    receipt = new_Transaction.receipt
    session.close()
    return True, receipt


# This function is very important and validates every transaction that a customer makes on the website. This is to
# prevent a user editing their cookies and creating an invalid transaction, and it checks to make sure that
# the transaction that was made was valid. This works as follows:
# - A dictionary of dictionaries is created that will contain dates for all days the customer has booked a room of that
# specific type. This prevents a user booking a 'phantom room', which is a room that appears to exist before the
# transaction is made, but is in fact already booked by the user. EG. the database may hold that 3 standard rooms are
# available for a specific day, but the user may book 5 standard rooms for that day, and as the transaction has not been
# committed the database will still hold that the 3 rooms are still available, when infact they are already booked by
# the user. Hence each room's avilability is checked from the database to make sure it is above 0 for each day for each
# specific room booked, as well as making sure it hasn't already been booked by the user
# - The start and end date for each room is checked to make sure it is not longer than 2
# - the start date is checked to not be set after the end date
# - Both dates are checked to make sure that the room is not booked more than 6 months in advance
# - The total transaction cost must match the total cost of transaction stored in the cookie
# - If any of these specifications are false, then the function returns false as the booking is invalid, otherwise
# - the function returns true
def check_rooms(request):
    session = db.create_session()
    cookie_total_cost, rooms = return_rooms_from_cookie(request)
    prev_rooms_booked = defaultdict(dict)
    total_cost = 0

    logger.info(f"Checking rooms from cookie are valid")

    for room in rooms:
        room.start_date = datetime.datetime.strptime(room.start_date, "%Y-%m-%d").date()
        room.end_date = datetime.datetime.strptime(room.end_date, "%Y-%m-%d").date()
        if room.start_date >= room.end_date or room.end_date - room.start_date > datetime.timedelta(weeks=2):
            session.close()
            logger.info(f"Invalid: room booked for longer than 2 weeks")
            return False, 0
        if room.start_date >= datetime.date.today()+datetime.timedelta(days=31*6) or room.end_date >= datetime.date.today()+datetime.timedelta(days=31*6):
            session.close()
            logger.info(f"Invalid: room booked six months in advance")
            return False, 0
        start_date = room.start_date
        while start_date <= room.end_date: # Increments each of the booked rooms for a specific type for all the days it is booked for
            if start_date in prev_rooms_booked.keys():
                if room.room_id in prev_rooms_booked[start_date].keys():
                    prev_rooms_booked[start_date][room.room_id] += 1
                else:
                    prev_rooms_booked[start_date][room.room_id] = 1
            else:
                prev_rooms_booked[start_date][room.room_id] = 1
            start_date += datetime.timedelta(days=1)

    for room in rooms:
        availability = 200 # default is set to 200 has it will always be higher than the default availability of any room
        start_date = room.start_date
        while start_date <= room.end_date: # Traverses the days the room is booked for
            available_room = session.query(Avaliable_Room).filter(Avaliable_Room.date == start_date).first()
            if room.room_id == 0:
                if available_room.standard_room_availability-prev_rooms_booked[start_date][room.room_id] < availability:
                    availability = available_room.standard_room_availability-prev_rooms_booked[start_date][room.room_id]
                cost: Current_Price = session.query(Current_Price).filter(Current_Price.date == start_date).first()
                total_cost += int(cost.standard_room_price)
            elif room.room_id == 1:
                if available_room.executive_room_availability-prev_rooms_booked[start_date][room.room_id] < availability:
                    availability = available_room.executive_room_availability-prev_rooms_booked[start_date][room.room_id]
                cost = session.query(Current_Price).filter(Current_Price.date == start_date).first()
                total_cost += int(cost.executive_price)
            elif room.room_id == 2:
                if available_room.suite_one_availability-prev_rooms_booked[start_date][room.room_id] < availability:
                    availability = available_room.suite_one_availability-prev_rooms_booked[start_date][room.room_id]
                cost = session.query(Current_Price).filter(Current_Price.date == start_date).first()
                total_cost += int(cost.suite_one_price)
            elif room.room_id == 3:
                if available_room.suite_two_availability-prev_rooms_booked[start_date][room.room_id] < availability:
                    availability = available_room.suite_two_availability-prev_rooms_booked[start_date][room.room_id]
                cost = session.query(Current_Price).filter(Current_Price.date == start_date).first()
                total_cost += int(cost.suite_two_price)
            else:
                session.close()
                return False, 0
            start_date += datetime.timedelta(days=1)
        if availability < 0:
            logger.info(f"Invalid: room not available")
            session.close()
            return False, 0

    if cookie_total_cost != total_cost:
        logger.info(f"Invalid: cookie cost does not match total cost")
        session.close()
        return False, 0
    session.close()
    logger.info(f"Transaction is valid")
    return True, 0

# Each of the rooms that the user booked in their basket are returned from the user's cookie data. These are decoded
# and converted into room booking objects, and the total price is returned along with the rooms. The format of these
# cookies is determined in the transaction view
def return_rooms_from_cookie(request):
    session = db.create_session()
    total_cost = 0
    rooms = []
    num_rooms = 0

    logger.info(f"Returning rooms from user cookie")

    for i in range(5):
        if "basket_cookie:" + str(i) not in flask.request.cookies:  # Cookie does not exist
            break
        new_room_cookie = flask.request.cookies["basket_cookie:" + str(num_rooms)]
        room_data = new_room_cookie.split(":") # Booking cookie split into its individual value data
        if len(room_data) != 4: # Checks that the cookie contains the room id, arrival and departure date, and the total cost
            return False
        new_room = Room_Booking()
        room_id = session.query(Room_Data.room_id).filter(Room_Data.room_name == room_data[0].replace("\"", "")).first()
        if room_id[0] > 3 or room_id[0] < 0: # Checks the room id is valid
            return False
        new_room.room_id = room_id[0]
        new_room.start_date = room_data[1]
        new_room.end_date = room_data[2]
        total_cost += int(room_data[3])
        rooms.append(new_room)
        num_rooms += 1
    session.close()
    return total_cost, rooms


# This is executed for when a user wants to refund a transaction. This works by deleting the transaction, and each of
# the rooms in the transaction; however before deleting these the availability is increased for each room type that the
# user booked a room for, as that room is now free again. Trans_session refers to the transaction session that has
# already been established in the view, this is to prevent previous session objects being deleted when they are on a
# different thread
def delete_transaction(transaction: Transaction, trans_session):
    session = db.create_session()
    if not Transaction:
        return None
    logger.info(f"Deleting transaction for user {transaction.customer_id}")
    for room in transaction.booked_rooms:
        start_date = room.start_date
        end_date = room.end_date
        room_id = room.room_id
        while start_date <= end_date:
            if room_id == 0:
                avaliable_room = session.query(Avaliable_Room).filter(Avaliable_Room.date == start_date).first()
                avaliable_room.standard_room_availability += 1
            elif room_id == 1:
                avaliable_room = session.query(Avaliable_Room).filter(Avaliable_Room.date == start_date).first()
                avaliable_room.executive_room_availability += 1
            elif room_id == 2:
                avaliable_room = session.query(Avaliable_Room).filter(Avaliable_Room.date == start_date).first()
                avaliable_room.suite_one_availability += 1
            elif room_id == 3:
                avaliable_room = session.query(Avaliable_Room).filter(Avaliable_Room.date == start_date).first()
                avaliable_room.suite_two_availability += 1
            else:
                return False
            start_date += datetime.timedelta(days=1)
        trans_session.close()
        session.delete(room)
        logger.info(f"Room: {room.id} deleted")
    session.delete(transaction)
    session.commit()
    logger.info(f"Transaction: {transaction.transaction_id} deleted")
    session.close()
    return True


