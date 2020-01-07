import flask, datetime
import main.data.database_or_cookie_funcs as cf
from main.data.room_data import Room_Data
from main.data.current_prices import Current_Price

blueprint = flask.Blueprint("info", __name__)

# Contains all the pages related to displaying information to the user

@blueprint.route("/info/gallery")
def gallery():
    has_cookies = False
    if "cookie_accept" in flask.request.cookies:
        has_cookies = True
    account_id = cf.check_valid_account_cookie(flask.request)
    if account_id:
        customer = cf.return_customer(account_id)
        if not customer:
            customer_name = None
        else:
            customer_name = customer.first_name.capitalize()
    else:
        customer_name = None
    return flask.render_template("/info/gallery.html", has_cookie=has_cookies, nav=True, footer=True,
                                         user_name=customer_name)


@blueprint.route("/info/accommodation")
def room_overview():
    has_cookies = False
    if "cookie_accept" in flask.request.cookies:
        has_cookies = True
    account_id = cf.check_valid_account_cookie(flask.request)
    if account_id:
        customer = cf.return_customer(account_id)
        if not customer:
            customer_name = None
        else:
            customer_name = customer.first_name.capitalize()
    else:
        customer_name = None

    return flask.render_template("/info/room.html", has_cookie=has_cookies, nav=True, footer=True,
                                     user_name=customer_name)


@blueprint.route("/info/restuarant")
def restaurant_overview():
    has_cookies = False
    if "cookie_accept" in flask.request.cookies:
        has_cookies = True
    account_id = cf.check_valid_account_cookie(flask.request)
    if account_id:
        customer = cf.return_customer(account_id)
        if not customer:
            customer_name = None
        else:
            customer_name = customer.first_name.capitalize()
    else:
        customer_name = None

    return flask.render_template("/info/restuarant.html", has_cookie=has_cookies, nav=True, footer=True,
                                     user_name=customer_name)


# Is used for showing each of the four room types
@blueprint.route("/info/room/<int:room_id>")
def room_specific(room_id: int):
    has_cookies = False
    if "cookie_accept" in flask.request.cookies:
        has_cookies = True
    account_id = cf.check_valid_account_cookie(flask.request)
    if account_id:
        customer = cf.return_customer(account_id)
        if not customer:
            customer_name = None
        else:
            customer_name = customer.first_name.capitalize()
    else:
        customer_name = None

    if room_id > 4 or room_id < 1: # Checks valid room id is entered
        return flask.redirect("/info/room")

    room: Room_Data = cf.return_room_with_id(room_id-1)

    if not room:
        return flask.redirect("/info")

    name = room.room_name
    info = room.description.split(":") # Room description is returned and the specification is displayed
    description = info[0]
    specification = info[1].split(",")

    returned_available_rooms = cf.return_available_rooms_inbetween_dates((datetime.date.today()-datetime.timedelta(days=1)).strftime("%Y-%m-%d"), (datetime.date.today()).strftime("%Y-%m-%d"))

    available_rooms = [0, 0, 0, 0] # Avaliable rooms are returned and displayed
    if returned_available_rooms:
        available_rooms[0] = returned_available_rooms[0].standard_room_availability
        available_rooms[1] = returned_available_rooms[0].executive_room_availability
        available_rooms[2] = returned_available_rooms[0].suite_one_availability
        available_rooms[3] = returned_available_rooms[0].suite_two_availability

    room_cost = cf.return_room_costs((datetime.date.today()-datetime.timedelta(days=1)).strftime("%Y-%m-%d"), (datetime.date.today()).strftime("%Y-%m-%d"))

    today_cost = [0, 0, 0, 0] # Current room cost is returned and displayed
    if room_cost:
        today_cost[0] = room_cost[0].standard_room_price
        today_cost[1] = room_cost[0].executive_price
        today_cost[2] = room_cost[0].suite_one_price
        today_cost[3] = room_cost[0].suite_two_price

    return flask.render_template("/info/specific_room.html", name=name, description=description, specification=specification,
                          available_rooms=available_rooms, today_cost=today_cost, has_cookies=has_cookies,
                          nav=True, footer=True, user_name=customer_name)


