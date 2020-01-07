import flask

blueprint = flask.Blueprint("misc", __name__)

# Contains all pages which are not essential to the website but are helpful to the user

@blueprint.route("/misc/help")
def help():
    has_cookies = False
    if "cookie_accept" in flask.request.cookies:
        has_cookies = True
    return flask.render_template("/misc/help.html", has_cookie=has_cookies, nav=False, footer=False)


@blueprint.route("/misc/policy_info")
def policy():
    has_cookies = False
    if "cookie_accept" in flask.request.cookies:
        has_cookies = True
    return flask.render_template("/misc/policy_info.html", has_cookie=has_cookies, nav=False, footer=True)


@blueprint.route("/misc/contact_us")
def contact_us():
    has_cookies = False
    if "cookie_accept" in flask.request.cookies:
        has_cookies = True
    return flask.render_template("/misc/contact_us.html", has_cookie=has_cookies, nav=False, footer=True)

