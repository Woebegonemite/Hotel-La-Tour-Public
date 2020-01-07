import flask, datetime, re
import main.data.database_or_cookie_funcs as cf
from main.data.room_data import Room_Data

blueprint = flask.Blueprint("account", __name__)

# Holds all the views related to creating and maintaining the user's account

@blueprint.route("/account/login", methods=["GET"])
def login_get():
    has_cookies = False
    if "cookie_accept" in flask.request.cookies:
        has_cookies = True
    account_id = cf.check_valid_account_cookie(flask.request)
    if account_id:
        customer = cf.return_customer(account_id)
        if customer:
            return flask.redirect("/") # Returns the customer to the index page if they are already logged in

    return flask.render_template("/account/register_login.html", has_cookie=has_cookies, nav=True, footer=True,
                                 page_type="login")


@blueprint.route("/account/login", methods=["POST"])
def login_post(): # Mainly
    data_form = flask.request
    password_first = data_form.form.get('password')
    email = data_form.form.get('email')
    server_error = cf.check_if_input_error(password_first)  # Checks if password is valid

    if len(password_first) < 8 or len(password_first) > 15:
        server_error = "Input error: password is not of correct size (8-15)"

    elif not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email):  # Validates email
        server_error = "Input Error: Email not in valid format"

    if server_error:  # Returns page if error is found
        return flask.render_template("account/register_login.html", page_type="login", ServerError=server_error,
                                     email=email, has_cookie=True, nav=True, footer=True)

    user = cf.check_user_is_in_database_and_password_valid(email, password_first)
    if not user:  # Checks if the user actually exists
        return flask.render_template("account/register_login.html", page_type="login",
                                     ServerError="Input error: Incorrect email or password",
                                     email=email, has_cookie=True, nav=True, footer=True)
    response = flask.redirect('/account/your_account')
    cf.set_auth(response, user.id)  # Creates user cookie
    return response


@blueprint.route("/account/register")
def register_get():
    has_cookies = False
    if "cookie_accept" in flask.request.cookies:
        has_cookies = True
    account_id = cf.check_valid_account_cookie(flask.request)
    if account_id:
        customer = cf.return_customer(account_id)
        if customer:
            return flask.redirect("/") # Returns user to home page if they are logged in

    return flask.render_template("/account/register_login.html", has_cookie=has_cookies, nav=True, footer=True,
                                 page_type="register")


# Handles register request
@blueprint.route("/account/register", methods=["POST"])
def register_post():
    data_form = flask.request
    title = data_form.form.get("title")
    password_first = data_form.form.get('password_first')
    password_second = data_form.form.get('password_second')
    first_name = data_form.form.get('first_name')
    last_name = data_form.form.get('last_name')
    email = data_form.form.get('email')
    tel_number = data_form.form.get('tel_number')
    dob = data_form.form.get('dob')
    postcode = data_form.form.get('postcode')
    address = data_form.form.get('address')
    country = data_form.form.get('country')
    city = data_form.form.get('city')
    email_sub = data_form.form.get('promotional')
    current_date = datetime.date.today()

    fields_to_check = [password_first, first_name, last_name, tel_number, postcode, address, city]
    for field in fields_to_check:
        server_error = cf.check_if_input_error(field) # Checks that the important fields are not invalid
                                                     # (hold special characters and are of the correct length)
        if server_error:
            break

    if len(title) > 5:
        server_error = "Input Error: Title is not valid"
    elif len(password_first) < 8 or len(password_first) > 15:
        server_error = "Input error: password is not of correct size (8-15)"
    elif len(address) < 10 or len(address) > 40:
        server_error = "Input error: address is not of correct size (8-15)"
    elif len(first_name) < 3 or len(first_name) > 15 or len(last_name) < 3 or len(last_name) > 15:
        server_error = "Input error: first name or last name of incorrect length"
    elif len(tel_number) > 11 or len(tel_number) < 7:
        server_error = "Input error: telephone of incorrect length"
    elif len(country) > 5 or len(country) < 2:
        server_error = "Input error: country of incorrect length"
    elif len(city) < 5 or len(city) > 20:
        server_error = "Input error: city of incorrect length"

    date_values = dob.split("-")
    formatted_dob = datetime.date(int(date_values[0]), int(date_values[1]), int(date_values[2]))
    if not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email):  # Validates email
        server_error = "Input Error: Email not in valid format"
    elif not re.fullmatch( # Validates postcode based on the regex provided by the Government
            r"([Gg][Ii][Rr] 0[Aa]{2})|((([A-Za-z][0-9]{1,2})|(([A-Za-z][A-Ha-hJ-Yj-y][0-9]{1,2})|(([A-Za-z][0-9][A-Za-z])|([A-Za-z][A-Ha-hJ-Yj-y][0-9][A-Za-z]?))))\s?[0-9][A-Za-z]{2})",
            postcode):
        server_error = "Input Error: Post code not in valid format"
    elif not tel_number.isnumeric(): # Telephone can only contain numbers
        server_error = "Input Error: telephone not in valid format"
    elif cf.check_if_email_exists(email):  # Checks if email exists in database
        server_error = "Input Error: Email already exists"
    elif password_first != password_second:  # Checks that both passwords match
        server_error = "Input Error: Passwords do not match"
    elif " " in password_first:
        server_error = "Input Error: Password cannot contain spaces"
    elif not any(num in password_first for num in ["1","2","3","4","5","6","7","8","9"]): # Checks password has a number
        server_error = "Input Error: Password must contain a number"
    elif formatted_dob > current_date - datetime.timedelta(days=365 * 16):  # Checks that user is over 16
        server_error = "Input Error: Incorrect date of birth entered (must be over 16)"

    if server_error:
        return flask.render_template("account/register_login.html", page_type="register",
                                     ServerError=server_error, email=email, date_of_birth=str(dob), first_name=first_name,
                                     last_name=last_name, postcode=postcode, address=address, title=title,
                                     city=city, email_sub=email_sub, tel_number=tel_number, nav=True, footer=True,)

    customer = cf.create_customer(title, password_first, first_name, last_name, email, tel_number, formatted_dob,
                                  postcode, address, country, city, email_sub) # Creates customer
    response = flask.redirect('/account/your_account')
    cf.set_auth(response, customer.id)  # Creates user cookie
    return response


@blueprint.route("/account/add_connection", methods=["GET"])
def connection_get():
    has_cookies = False
    if "cookie_accept" in flask.request.cookies:
        has_cookies = True
    account_id = cf.check_valid_account_cookie(flask.request)
    if account_id:
        customer = cf.return_customer(account_id)
        if not customer:
            response = flask.redirect('/account/login')
            cf.destroy_cookie(response)
            return response
    else:
        return flask.redirect('/account/login')

    pending_friends = cf.return_pending_connections(account_id) # Returns all pending friends

    return flask.render_template("/account/user_connect.html", has_cookie=has_cookies, nav=True, footer=True,
                                 user_name=customer.first_name.capitalize(), user_id=account_id,
                                 pending_friends=pending_friends)


@blueprint.route("/account/add_connection", methods=["POST"])
def connection_post():
    has_cookies = False
    if "cookie_accept" in flask.request.cookies:
        has_cookies = True
    account_id = cf.check_valid_account_cookie(flask.request)
    if account_id:
        customer = cf.return_customer(account_id)
        if not customer:
            response = flask.redirect('/account/login')
            cf.destroy_cookie(response)
            return response
    else:
        return flask.redirect('/account/login')

    data_form = flask.request

    if data_form.form.get("AcceptPending") or data_form.form.get("DeclinePending"):
        pending_user_id = data_form.form.get("connected_id")
        pending_user = cf.return_customer(pending_user_id)

        if data_form.form.get("AcceptPending"): # If the user has accepted a friend request then the connection is established
            if not cf.update_connection(pending_user_id,customer.id):
                return flask.abort(500)
            pending_friends = cf.return_pending_connections(account_id)
            return flask.render_template("/account/user_connect.html", has_cookie=has_cookies, nav=True, footer=True,
                                         user_name=customer.first_name.capitalize(), user_id=account_id, success=2,
                                         added_email=pending_user.email,pending_friends=pending_friends)

        elif data_form.form.get("DeclinePending"): # If the user declines a friend request then the connection is removed
            if not cf.delete_connection(pending_user_id, customer.id):
                return flask.abort(500)
            pending_friends = cf.return_pending_connections(account_id)
            return flask.render_template("/account/user_connect.html", has_cookie=has_cookies, nav=True, footer=True,
                                         user_name=customer.first_name.capitalize(), user_id=account_id, success=3,
                                         added_email=pending_user.email,pending_friends=pending_friends)

    elif data_form.form.get("DeleteFriend"): # If the user chooses to delete a friend then the connection is destroyed
        deleted_user_email = data_form.form.get("deleted_email")
        deleted_user = cf.return_customer_with_email(deleted_user_email)
        server_error = None

        if deleted_user_email == customer.email:
            server_error = "Input Error: Cannot enter your own email"
        elif not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", deleted_user_email):  # Validates email
            server_error = "Input Error: Email not in valid format"
        elif not deleted_user:
            server_error = "Input Error: Email does not exists"
        elif deleted_user == customer.email:
            server_error = "Input Error: Cannot add yourself as a friend"
        elif not cf.check_connection_already_pending_or_exists(customer.id,deleted_user.id) and not cf.check_connection_already_pending_or_exists(deleted_user.id,customer.id):
            server_error = f"Input Error: Connection does not exist between you and {deleted_user_email}"

        pending_friends = cf.return_pending_connections(account_id)

        if server_error:
            return flask.render_template("/account/user_connect.html", has_cookie=has_cookies, nav=True, footer=True,
                                         user_name=customer.first_name.capitalize(), user_id=account_id,
                                         error=server_error)

        cf.delete_connection(customer.id, deleted_user.id)

        return flask.render_template("/account/user_connect.html", has_cookie=has_cookies, nav=True, footer=True,
                                     user_name=customer.first_name.capitalize(), user_id=account_id, success=4,
                                     added_email=deleted_user_email, pending_friends=pending_friends)


    elif data_form.form.get("AddFriend"): # If the user chose to add a friend, then a pending connection is established
        server_error = None
        add_email = data_form.form.get("email")
        if not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", add_email):  # Validates email
            server_error = "Input Error: Email not in valid format"
        elif add_email == customer.email:
            server_error = "Input Error: Cannot add yourself as a friend"
        else:
            user_connection = cf.return_customer_with_email(add_email)
            if not user_connection:
                server_error = "Input Error: User of that email does not exist"
            elif cf.check_connection_already_pending_or_exists(customer.id, user_connection.id):
                server_error = "Input Error: Connection already exists"

        pending_friends = cf.return_pending_connections(account_id)

        if server_error:
            return flask.render_template("/account/user_connect.html", has_cookie=has_cookies, nav=True, footer=True,
                                         user_name=customer.first_name.capitalize(), user_id=account_id,
                                         error=server_error)

        cf.create_connection(customer.id, user_connection.id)  # Connection is established

        return flask.render_template("/account/user_connect.html", has_cookie=has_cookies, nav=True, footer=True,
                                     user_name=customer.first_name.capitalize(), user_id=account_id, success=1,
                                     added_email=add_email,pending_friends=pending_friends)

    return flask.abort(404)


@blueprint.route("/account/your_account")
def view_account():
    has_cookies = False
    if "cookie_accept" in flask.request.cookies:
        has_cookies = True
    account_id = cf.check_valid_account_cookie(flask.request)
    if account_id:
        customer = cf.return_customer(account_id)
        if not customer:
            response = flask.redirect('/account/login')
            cf.destroy_cookie(response)
            return response
    else:
        return flask.redirect('/account/login')

    num_connections = len(customer.friends) # Returns the number of user connections
    num_transactions = len(customer.bookings) # Returns the number of transactions the user has made
    upcoming_transactions = []
    friend_activity = []

    for transaction in customer.bookings: # Returns upcoming bookings
        for room_booking in transaction.booked_rooms:
            if room_booking.end_date > datetime.date.today():
                room: Room_Data = cf.return_room_with_id(room_booking.room_id)
                upcoming_transactions.append([room.room_name, room_booking.start_date.strftime("%m/%d/%Y"),
                                              room_booking.end_date.strftime("%m/%d/%Y"),room_booking.booking_id])

    friends = cf.return_established_connections(customer.id)

    for friend in friends: # Returns all upcoming rooms booked by friends
        new_friend = cf.return_customer(friend.id)
        for friend_transactions in new_friend.bookings:
            for friend_bookings in friend_transactions.booked_rooms:
                if friend_bookings.end_date > datetime.date.today():
                    room: Room_Data = cf.return_room_with_id(friend_bookings.room_id)
                    friend_activity.append([friend.first_name.capitalize(), friend.first_name.capitalize() +
                                            " " + friend.last_name.capitalize() + " (" + str(friend.id) + ")",
                                                  room.room_name, friend_bookings.start_date.strftime("%m/%d/%Y"),
                                                  friend_bookings.end_date.strftime("%m/%d/%Y")])

    # Sorts bookings in order of arrival date
    friend_activity.sort(key=lambda current_activity: datetime.datetime.strptime(current_activity[3], "%m/%d/%Y"))

    return flask.render_template("/account/your_account.html", has_cookie=has_cookies, nav=True, footer=True,
                                 user_name=customer.first_name.capitalize(), customer=customer,
                                 upcoming_transactions=upcoming_transactions, num_connections=num_connections,
                                 num_transactions=num_transactions, friend_activity=friend_activity)


@blueprint.route('/log_out', methods=["GET"])
def log_out():
    response = flask.redirect("/")
    cf.destroy_cookie(response) # User cookie is destroyed and they are logged out
    for i in range(5):  # Basket cookies are destroyed
        if "basket_cookie:" + str(i) in flask.request.cookies:
            response.set_cookie("basket_cookie:" + str(i), "", expires=0)  # Sets cookie to expire immediately
    return response


@blueprint.route('/account/change_password', methods=["GET"])
def change_password_get():
    has_cookies = False
    if "cookie_accept" in flask.request.cookies:
        has_cookies = True
    account_id = cf.check_valid_account_cookie(flask.request)
    if account_id:
        customer = cf.return_customer(account_id)
        if not customer:
            response = flask.redirect('/account/login')
            cf.destroy_cookie(response)
            return response
    else:
        return flask.redirect('/account/login')

    return flask.render_template("/account/change_password.html", has_cookie=has_cookies, old_pass=True)


@blueprint.route('/account/change_password', methods=["POST"])
def change_password_post():
    has_cookies = False
    if "cookie_accept" in flask.request.cookies:
        has_cookies = True
    account_id = cf.check_valid_account_cookie(flask.request)
    if account_id:
        customer = cf.return_customer(account_id)
        if not customer:
            response = flask.redirect('/account/login')
            cf.destroy_cookie(response)
            return response
    else:
        return flask.redirect('/account/login')

    data_form = flask.request

    if data_form.form.get('submitOldPassword'):
        print("HELLO")
        passwordCurrent =  data_form.form.get('passwordCurrent')
        if len(passwordCurrent) < 8 or len(passwordCurrent) > 15:
            server_error = "Input error: password is not of correct size (8-15)"
        elif " " in passwordCurrent:
            server_error = "Input Error: Password cannot contain spaces"
        elif not any(num in passwordCurrent for num in["1", "2", "3", "4", "5", "6", "7", "8", "9"]):  # Checks password has a number
            server_error = "Input Error: Password must contain a number"
        else:
            server_error = cf.check_if_input_error(passwordCurrent)

        if not cf.verify_hash(customer.password,passwordCurrent):
            server_error = "Input Error: Password does not match stored password"

        if server_error:
            return flask.render_template("/account/change_password.html", has_cookie=has_cookies, old_pass=True, ServerError=server_error)
        else:
            return flask.render_template("/account/change_password.html", has_cookie=has_cookies, old_pass=False)

    else:
        password_New = data_form.form.get('password_New')
        password_Retype = data_form.form.get('password_Retype')
        if len(password_New) < 8 or len(password_New) > 15:
            server_error = "Input error: password is not of correct size (8-15)"
        elif " " in password_New:
            server_error = "Input Error: Password cannot contain spaces"
        elif not any(num in password_New for num in["1", "2", "3", "4", "5", "6", "7", "8", "9"]):  # Checks password has a number
            server_error = "Input Error: Password must contain a number"
        elif password_New != password_Retype:
            server_error = "Input Error: Passwords must match"
        else:
            server_error = cf.check_if_input_error(password_New)

        if server_error:
            return flask.render_template("/account/change_password.html", has_cookie=has_cookies, old_pass=False, ServerError=server_error)

        else:
            valid = cf.change_user_password(customer.id, password_New)
            return flask.render_template("/account/change_password.html", has_cookie=has_cookies, success=True)