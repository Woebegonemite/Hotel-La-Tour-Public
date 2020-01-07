import flask, jsonify, datetime
import main.data.database_or_cookie_funcs as cf

blueprint = flask.Blueprint("AJAX", __name__)

# Executed if the user enters in an email by checking if it exists
@blueprint.route("/get_email_val")
def email_val():
    data_form = flask.request

    email = data_form.form.get("email")

    if not email:
        return jsonify({"result":"invalid"})

    if cf.check_if_email_exists(email):
        return jsonify({"result": "valid"})

    return jsonify({"result": "invalid"})
