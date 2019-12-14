"""OpenAQ Air Quality Dashboard with Flask."""
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import openaq
from . import settings

# instantiate the app
APP = Flask(__name__)
# configure settings
APP.config.from_object(settings)
# instantiate the database
DB = SQLAlchemy(APP)


class Record(DB.Model):
    """This is the mapping for records returned from the openaq api

    The openaq api is a free api that returns air quality information from
    all around the world.

    """
    id = DB.Column(DB.Integer, primary_key=True)
    datetime = DB.Column(DB.String(25))
    value = DB.Column(DB.Float, nullable=False)
    city = DB.Column(DB.String(500), nullable=False)
    country = DB.Column(DB.String(20), nullable=False)

    def __repr__(self):
        return f"<Record(datetime={self.datetime}, value={self.value}"


@APP.route('/refresh')
def refresh():
    """Pull fresh data from Open AQ and replace existing data."""
    DB.drop_all()
    DB.create_all()
    records = process_results()
    save_observations(records)
    DB.session.commit()
    return """
    <script>
        setTimeout("location.href = '/';",3000);
    </script>
    <h2>Data refreshed!</h2> redirecting back to homepage...."""


@APP.route('/')
def root():
    """Base view."""
    records = Record.query.filter(Record.value >= 10).all()
    return render_template('home/index.html', records=records)


def process_results(city="Los Angeles", parameter="pm25"):
    """returns [(utc date), (value), (city), (country)]

    Pulls data from the openaq api and process the results to return a list
    of tuples with the observation utc time, air quality value, the city,
    and country that the observation was taken in.
    """
    api = openaq.OpenAQ()
    status, body = api.measurements(city=city, parameter=parameter)
    res = body['results']
    results = [(x['date']['utc'], x['value'], x['city'], x['country'])
               for x in res]

    return results


def save_observations(records):
    """Process and save records to database"""
    entries = [Record(datetime=str(record[0]), value=record[1], city=record[
        2], country=record[3]) for record in records]

    DB.session.add_all(entries)
    DB.session.commit()
