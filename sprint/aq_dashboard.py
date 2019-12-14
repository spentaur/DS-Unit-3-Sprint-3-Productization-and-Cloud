"""OpenAQ Air Quality Dashboard with Flask."""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import openaq

APP = Flask(__name__)

APP.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
DB = SQLAlchemy(APP)


class Record(DB.Model):
    id = DB.Column(DB.Integer, primary_key=True)
    datetime = DB.Column(DB.String(25))
    value = DB.Column(DB.Float, nullable=False)

    def __repr__(self):
        return f"<Record(datetime={self.datetime}, value={self.value}"


@APP.route('/refresh')
def refresh():
    """Pull fresh data from Open AQ and replace existing data."""
    DB.drop_all()
    DB.create_all()
    records = process_time_and_value()
    save_time_and_value(records)
    DB.session.commit()
    return 'Data refreshed!'


@APP.route('/')
def root():
    """Base view."""
    records = Record.query.filter(Record.value >= 10).all()
    return str([(res.datetime, res.value) for res in records])


def process_time_and_value(city="Los Angeles", parameter="pm25"):
    api = openaq.OpenAQ()
    status, body = api.measurements(city=city, parameter=parameter)
    res = body['results']
    time_and_value = [(x['date']['utc'], x['value']) for x in res]

    return time_and_value


def save_time_and_value(records):
    entries = [Record(datetime=str(record[0]), value=record[1]) for record in
               records]

    DB.session.add_all(entries)
    DB.session.commit()
