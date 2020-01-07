import flask
import main.data.database_or_cookie_funcs as cf

blueprint = flask.Blueprint("index", __name__)

#  Displays the index page
@blueprint.route("/")
def index_view():
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

    return flask.render_template("/index/index.html", has_cookie=has_cookies, nav=True, footer=True,
                                     user_name=customer_name)


