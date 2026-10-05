from flask import Flask, jsonify

from app.data_storage import start_comm_thread
from app.data_storage import data_store

# creation of the main app instance
def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        START_COMM_THREAD=True
    )

    # if configuration for the test has been passed, update the app configuration
    if test_config:
        app.config.update(test_config)


    # starting a thread that reads the values from arduino
    if app.config["START_COMM_THREAD"]:
        start_comm_thread()

    # definition of the index page
    from . import landing
    app.register_blueprint(landing.bp)
    app.add_url_rule('/', endpoint='index')

    # defining the api endpoint to get the weather parameters
    @app.route("/api/weather")
    def weather():
        data = data_store.get()
        # loading global weather data and parsing it to JSON
        return jsonify({
            "temperature": data.get('temperature'),
            "humidity": data.get('humidity')
        })


    return app