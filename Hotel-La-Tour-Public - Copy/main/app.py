import flask, os, sys, logging
import main.data.db_session as db


folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, folder)

app = flask.Flask(__name__)


# App is configured and ran
def main():
    configure()
    app.run(debug=True)


# App is configured
def configure():
    print("Configuring Flask app:")

    register_blueprints()
    print("Registered blueprints")

    setup_db()
    print("DB setup completed.")

    create_logging()
    print("Logging created")

    print("Starting application:")


# Database is setup
def setup_db():
    db_file = os.path.join(
        os.path.dirname(__file__),
        'db',
        'HotelLaTour.sqlite')
    db.global_init(db_file)


# All app blueprints are added
def register_blueprints():
    from main.views import index_view
    from main.views import misc_view
    from main.views import info_view
    from main.views import account_view
    from main.views import transaction_view
    from main.views import dev_view
    from main.views import AJAX_view

    app.register_blueprint(index_view.blueprint)
    app.register_blueprint(misc_view.blueprint)
    app.register_blueprint(info_view.blueprint)
    app.register_blueprint(account_view.blueprint)
    app.register_blueprint(transaction_view.blueprint)
    app.register_blueprint(dev_view.blueprint)
    app.register_blueprint(AJAX_view.blueprint)


# Error logging is created so all errors are recorded
def create_logging():
    file_error_handler = logging.FileHandler("../logs/error_log.log")
    file_error_handler.setFormatter(logging.Formatter("%(asctime)s:%(module)s:%(message)s"))
    file_error_handler.setLevel(logging.WARNING)

    app.logger.addHandler(file_error_handler)


# Returns a 'not found' page if the route cannot be established
@app.errorhandler(404)
def page_not_found(Error):
    return flask.render_template('/misc/not_found.html', has_cookie=True, nav=False, footer=False), 404


@app.errorhandler(405)
def page_not_found(Error):
    return flask.render_template('/misc/not_found.html', has_cookie=True, nav=False, footer=False), 405


# Returns a 'server error' page if an error occurs
@app.errorhandler(500)
def page_not_found(Error):
    return flask.render_template('/misc/server_error.html', has_cookie=True, nav=False, footer=False), 500


if __name__ == '__main__':
    main()
else:
    configure()


