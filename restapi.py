from flask import Flask, Response, jsonify, send_from_directory, url_for, redirect
from flask_restful import Resource, Api
from flask.logging import default_handler
from database import DatabaseConnector
from gevent.pywsgi import WSGIServer
import logging

db = DatabaseConnector()
db.connect()


class Measurements(Resource):

    def get(self):
        records = db.get_measurement(limit=10)

        result = {}
        for record in records:
            sid = record[0]
            timestamp = record[1]
            station = record[2]
            temperature = record[3]
            humidity = record[4]

            result[sid] = {
                "timestamp": timestamp,
                "station": station,
                "temperature": temperature,
                "humidity": humidity
            }

        json = jsonify(result)
        return json


class MeasurementsChart(Resource):
    def get(self):
        temp_time_t1 = db.get_measurement_by_station(limit=30, station="T1")
        temp_time_t2 = db.get_measurement_by_station(limit=30, station="T2")

        labels = []
        t1 = []
        h1 = []
        t2 = []
        h2 = []

        for temp, hum, time in temp_time_t1:
            t1.append({"x": time, "y": temp})
            h1.append({"x": time, "y": hum})
            labels.append(time)

        for temp, hum, time in temp_time_t2:
            t2.append({"x": time, "y": temp})
            h2.append({"x": time, "y": hum})
            labels.append(time)

        labels = list(dict.fromkeys(labels))
        labels.sort()

        result = {"t1": t1,
                  "t2": t2,
                  "h1": h1,
                  "h2": h2,
                  "labels": labels}

        json = jsonify(result)
        return json


def run_server():
    app = Flask(__name__, static_url_path='/static')

    stream_handler = logging.StreamHandler()
    stream_formatter = logging.Formatter('%(levelname)s: %(msg)s')
    stream_handler.setFormatter(stream_formatter)

    logger = logging.getLogger()
    logger.handlers[0].setFormatter(stream_formatter)

    @app.route('/')
    def index():
        return redirect('/static/index.html')

    api = Api(app)
    api.add_resource(Measurements, '/measurements')
    api.add_resource(MeasurementsChart, '/chart')

    http_server = WSGIServer(("0.0.0.0", 8080), app, log=logger)
    http_server.serve_forever()