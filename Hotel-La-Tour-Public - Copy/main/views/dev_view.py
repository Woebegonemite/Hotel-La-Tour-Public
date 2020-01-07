import flask
import main.data.database_or_cookie_funcs as cf

blueprint = flask.Blueprint("dev", __name__)

# Contains all the views related to developer functions that can be performed

@blueprint.route("/dev/delete")
def delete_all():

    devs = ["lewis.stuart11@yahoo.co.uk"] # This page is only loaded if I am logged in

    account_id = cf.check_valid_account_cookie(flask.request)
    if account_id:
        customer = cf.return_customer(account_id)
        if not customer:
            return flask.abort(404)
        if customer.email.strip() in devs:
            cf.delete_all_from_database(devs)
            return flask.render_template("Success.html")

    return flask.abort(404)


@blueprint.route("/dev/fill")
def fill_database():
    devs = ["lewis.stuart11@yahoo.co.uk"]

    account_id = cf.check_valid_account_cookie(flask.request)
    if account_id:
        customer = cf.return_customer(account_id)
        if not customer:
            return flask.abort(404)
        if customer.email.strip() in devs:
            cf.update_database()
            return flask.render_template("Success.html")

    return flask.abort(404)