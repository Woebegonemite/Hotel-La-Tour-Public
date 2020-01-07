import flask, datetime
import main.data.database_or_cookie_funcs as cf
from main.data.room_data import Room_Data
from main.data.transaction import Transaction

blueprint = flask.Blueprint("transaction", __name__)


# Holds all views related with dealing with user transactions

@blueprint.route("/transaction/table_booking")
def table_booking():
    has_cookies = False
    if "cookie_accept" in flask.request.cookies:
        has_cookies = True
    return flask.render_template("/transactions/table_booking.html", has_cookie=has_cookies, nav=False, footer=False)


@blueprint.route("/transaction/booking")
def booking():
    has_cookies = False
    if "cookie_accept" in flask.request.cookies:
        has_cookies = True
    return flask.render_template("/transactions/booking.html", has_cookie=has_cookies, nav=True, footer=True)


@blueprint.route("/transaction/delete_transaction", methods=["GET"])
def delete_transaction_get():
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

    return flask.render_template("/transactions/delete_transaction.html", user_name=customer.first_name.capitalize(),
                                 has_cookie=has_cookies, nav=False, footer=False)


@blueprint.route("/transaction/delete_transaction", methods=["POST"])
def delete_transaction_post():
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

    data_form = flask.request.form

    if data_form.get(
            "submitConfirm") == "Cancel":  # User has chosen not to delete their transaction and thus the normal
        # page is displayed along with a message of confirmation that their
        # transaction has not been deleted
        return flask.render_template("/transactions/delete_transaction.html",
                                     user_name=customer.first_name.capitalize(),
                                     has_cookie=has_cookies, nav=False, footer=False, complete=2)

    receipt = data_form.get("receipt")

    error = None
    if not receipt:
        error = "Input Error: Receipt is not valid"

    transaction, session = cf.return_transaction_by_receipt(receipt)  # Receipt that the user entered is checked to make
    # it exists in the database
    if not transaction:
        error = "Input Error: Receipt does not exist for a transaction"
    elif transaction.customer_id != customer.id:
        error = "Input Error: Receipt does not belong to this account"

    if error:
        return flask.render_template("/transactions/delete_transaction.html",
                                     user_name=customer.first_name.capitalize(),
                                     has_cookie=has_cookies, nav=False, footer=False, error=error)

    if data_form.get("submitConfirm") == "Submit":  # User has confirmed that they want to delete their transaction
        valid = cf.delete_transaction(transaction, session)  # Transaction is attempted to be deleted
        if valid:  # Normal page is returned along with confirmation that it has been deleted
            return flask.render_template("/transactions/delete_transaction.html",
                                         user_name=customer.first_name.capitalize(),
                                         has_cookie=has_cookies, nav=False, footer=False, complete=1)
        else:  # Transaction could not be deleted and an error is returned
            return flask.render_template("/transactions/delete_transaction.html",
                                         user_name=customer.first_name.capitalize(),
                                         has_cookie=has_cookies, nav=False, footer=False,
                                         error="Unknown error occured, please contact us if this continues")


    else:  # The user has entered a receipt and the transaction data is returned
        transaction_data = []
        if transaction.booked_rooms:  # Each room booked and its information is returned for the transaction
            for room in transaction.booked_rooms:
                transaction_data.append([room.room_data.room_name, room.start_date, room.end_date])
            return flask.render_template("/transactions/delete_transaction.html",
                                         user_name=customer.first_name.capitalize(),
                                         has_cookie=has_cookies, nav=False, footer=False,
                                         transaction_data=transaction_data, transaction_type="room",
                                         cost=transaction.cost, receipt=receipt)
        else:
            for table in transaction.booked_tables:  # Each table booked is returned
                transaction_data.append([table.table_type, table.table_type])
            return flask.render_template("/transactions/delete_transaction.html",
                                         user_name=customer.first_name.capitalize(),
                                         has_cookie=has_cookies, nav=False, footer=False,
                                         transaction_data=transaction_data, transaction_type="table",
                                         cost=transaction.cost, receipt=receipt)


# Room booking page
@blueprint.route("/transaction/room_booking", methods=["POST", "GET"])
def room_booking():
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

    data_form = flask.request.form

    if data_form.get("CheckOut"):  # User checks out and the transaction is attempted to be added
        was_valid, receipt = cf.create_transaction_and_book_rooms(customer, flask.Request)
        if was_valid:
            response = flask.redirect("/Success/" + receipt)  # User is set to return to the success page
        else:
            response = flask.redirect("/Error")  # A fatal error has occured and the user is taken to the error page
        for i in range(5):  # Basket cookies are destroyed
            if "basket_cookie:" + str(i) in flask.request.cookies:
                response.set_cookie("basket_cookie:" + str(i), "", expires=0)  # Sets cookie to expire immediately
        return response

    else:
        rooms_booked = []
        num_room_types_booked = [0 for i in range(4)]

        search_start_date = data_form.get("Arrival")  # Search field values are returned
        search_end_date = data_form.get("Depart")
        search_cost = data_form.get("Price")
        room_type = data_form.get("RoomType")

        if not search_cost:  # If there is no price value posted, the default value of 'any' is used
            max_cost = 4000
            min_cost = 0
        else:
            min_cost = int(search_cost.split("-")[0])  # Search prices are returned
            max_cost = int(search_cost.split("-")[1])

        if not room_type:  # As default, the room type to return is set to any
            room_type = "Any"

        if not search_start_date:  # As default, the search dates are for tomorrow and the day after
            search_start_date = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            search_end_date = (datetime.date.today() + datetime.timedelta(days=2)).strftime("%Y-%m-%d")
        search_data = {
            'cost': str(min_cost) + "-" + str(max_cost),
            'type': room_type,
            'start_date': search_start_date,
            'end_date': search_end_date
        }

        num_rooms = 0
        for i in range(5):  # Basket cookie data is traveresd
            if "basket_cookie:" + str(i) not in flask.request.cookies:  # Cookie does not exist
                break
            else:  # User has booked a room, and the room data is decoded and the number of rooms booked is incremented by 1
                num_rooms += 1
                cookie_room_type = flask.request.cookies["basket_cookie:" + str(i)].split(":")[0].replace("\"", "")
                if cookie_room_type == "Standard Room":
                    num_room_types_booked[0] += 1
                elif cookie_room_type == "Executive Room":
                    num_room_types_booked[1] += 1
                elif cookie_room_type == "Suite One":
                    num_room_types_booked[2] += 1
                elif cookie_room_type == "Suite Two":
                    num_room_types_booked[3] += 1

        delete_all = data_form.get("DeleteBasket")  # User has chosen to delete all from their basket
        if delete_all:
            response = flask.redirect("/transaction/room_booking")
            for i in range(num_rooms + 1):  # All basket cookies are set to 0
                response.set_cookie("basket_cookie:" + str(i), "", expires=0)  # Sets cookie to expire immediately
            return response

        room_id_to_add = data_form.get("room_add")
        if room_id_to_add:  # User has chosen to add a specific room
            room_data: Room_Data = cf.return_room_with_id(
                int(room_id_to_add))  # Room data for the added room is returned
            response = flask.redirect("/transaction/room_booking")

            # New cookie is created for the added room
            cf.create_basket_cookie(num_rooms, room_data.room_name, search_start_date, search_end_date,
                                    int(data_form.get("room_add_cost")), response)
            return response

        num_rooms_available_for_days = cf.return_available_rooms_inbetween_dates(search_start_date, search_end_date)
        all_room_costs = cf.return_room_costs(search_start_date, search_end_date)
        if not num_rooms_available_for_days or not all_room_costs:  # The user has not entered valid dates or a valid price range
            # So the default page is returned and displayed
            return flask.render_template("/transactions/room_booking.html", has_cookie=has_cookies, nav=True,
                                         footer=True,
                                         rooms_booked=rooms_booked, search_data=search_data,
                                         num_rooms=num_rooms, user_name=customer.first_name.capitalize())

        final_room_data_aval = [200 for i in
                                range(4)]  # Used to return the value of the lowest available room for each type

        show_room = [Room() for i in range(4)]  # Stores whether to show a room or not

        total_room_costs = [0 for i in range(4)]  # Stores the total room costs for the four room types

        for day_cost in all_room_costs:  # Total cost for each room type is deduced
            current_room_cost = [day_cost.standard_room_price, day_cost.executive_price,
                                 day_cost.suite_one_price, day_cost.suite_two_price]
            for i in range(4):
                total_room_costs[i] += current_room_cost[i]

        for room in num_rooms_available_for_days:  # Calculates the lowest availability for each room type by
            # traversing all the days the user has searched for and comparing
            # and comparing the availability to the previous days, if
            # it is lower than the new lowest room availability is set
            # this also subtracts the previous rooms booked of that type
            current_room_aval = [room.standard_room_availability, room.executive_room_availability,
                                 room.suite_one_availability, room.suite_two_availability]
            for i in range(4):
                if room_type == "Any":
                    if final_room_data_aval[i] > current_room_aval[i] - num_room_types_booked[i]:
                        final_room_data_aval[i] = current_room_aval[i] - num_room_types_booked[i]
                elif i == int(room_type) - 1:
                    if final_room_data_aval[i] > current_room_aval[i] - num_room_types_booked[i]:
                        final_room_data_aval[i] = current_room_aval[i] - num_room_types_booked[i]
                else:
                    continue

        for i in range(4): # Used for determining whether to show a room of a certain type of not
            add_room = False
            if total_room_costs[i] > max_cost or total_room_costs[i] < min_cost: # Total room cost does not match price range
                show_room[i] = None
            elif final_room_data_aval[i] <= 0: # Room of certain type if not available
                show_room[i] = None
            elif room_type != 'Any':
                if int(room_type) != i + 1: # Room type search field does not match current room type
                    show_room[i] = None
                else:
                    add_room = True
            else:
                add_room = True

            if add_room: # Room should be shown, thus all room data is calculated and the room is added
                show_room[i].start_date = search_start_date
                show_room[i].end_date = search_end_date
                show_room[i].total_cost = total_room_costs[i]
                show_room[i].id = i
                returned_room: Room_Data = cf.return_room_with_id(i)
                show_room[i].room_name = returned_room.room_name
                show_room[i].description = returned_room.description.split(":")[0]

        return flask.render_template("/transactions/room_booking.html", has_cookie=has_cookies, nav=True, footer=True,
                                     final_room_data=show_room, rooms_booked=rooms_booked, search_data=search_data,
                                     num_rooms=num_rooms, user_name=customer.first_name.capitalize())

# Class defining all the room data that should be shown to the user
class Room:
    room_name: str
    description: str
    start_date: datetime.date
    end_date: datetime.date
    total_cost: int
    index: int
    id: int


# This page is shown once a user has successfully deleted a room
@blueprint.route("/Success/<reciept>", methods=["POST", "GET"])
def success(reciept):
    account_id = cf.check_valid_account_cookie(flask.request)
    if account_id:
        customer = cf.return_customer(account_id)
        if not customer:
            response = flask.redirect('/account/login')
            cf.destroy_cookie(response)
            return response
    else:
        return flask.redirect('/account/login')
    return flask.render_template("/Success.html", reciept=reciept)


@blueprint.route("/Error", methods=["POST", "GET"])
def error():
    return flask.render_template("/misc/server_error.html")
