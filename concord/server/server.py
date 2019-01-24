# -*- coding: utf-8 -*-

"""Flask server definition"""

import os
from datetime import datetime
from logging import getLogger

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from flask import Flask, render_template, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

__log__ = getLogger(__name__)

APP = Flask(__name__)
DEFAULT_SQLITE_PATH = 'sqlite:///concord.db'
APP.config['SQLALCHEMY_DATABASE_URI'] = DEFAULT_SQLITE_PATH
db = SQLAlchemy(APP)


class Member(db.Model):
    id = db.Column(db.String(80), primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    messages = db.relationship('Message', backref='member', lazy=True)


class Server(db.Model):
    id = db.Column(db.String(80), primary_key=True)
    name = db.Column(db.String(80), nullable=False)


class Channel(db.Model):
    id = db.Column(db.String(80), primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    server = db.Column(db.String(80), db.ForeignKey('server.id'),
                       nullable=False)


class Message(db.Model):
    id = db.Column(db.String(80), primary_key=True)
    author = db.Column(db.String(80), db.ForeignKey('member.id'),
                       nullable=False)
    timestamp = db.Column(db.DateTime)
    channel_id = db.Column(db.String(80), db.ForeignKey('channel.id'),
                           nullable=False)
    channel = db.relationship('Channel', backref='channel_messages', lazy=True)
    content = db.Column(db.UnicodeText(), nullable=True)


##################
# main frontend
##################


@APP.route('/', methods=["GET"])
def index():
    # parse request arguments
    return render_template('index.html')


@APP.route('/static/<path:path>')
def static_file(path):
    static_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static')
    return send_from_directory(static_folder, path)


##################
# dash frontend
##################


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

DASH = dash.Dash(__name__, server=APP, external_stylesheets=external_stylesheets)


slider_dates = {
    0: "Year",
    1: "Month",
    2: "Day",
    3: "Hour",
    4: "Minute",
    5: "Second"
}

date_bins = {
    0: "%Y",
    1: "%Y-%m",
    2: "%Y-%m-%d",
    3: "%Y-%m-%d-%H",
    4: "%Y-%m-%d-%H:%M",
    5: "%Y-%m-%d-%H:%M:%S"  # TODO: does not work very well should remove?
}

DASH.layout = html.Div(
    style={
        "overflow-x": "hidden"
    },
    children=[
        dcc.Dropdown(
            id='discord-server-dropdown',
            options=[{}],
            multi=True,
            placeholder="Select a Discord Server..."
        ),
        dcc.DatePickerRange(
            id='message-date-picker-range',
            end_date=datetime.utcnow(),
            start_date=datetime(2015, 5, 13)  # discord launch date
        ),
        dcc.Graph(
            id='member-messages-graph',
            figure={
                'data': [
                    {
                        'x': [],
                        'y': [],
                        'type': 'bar',
                        'name': 'SF'
                    },
                ],
                'layout': {
                    'title': 'Dash Data Visualization',
                }
            }
        ),
        html.Div(
            children=[
                dcc.Slider(
                    id="date-binning-slider",
                    min=0,
                    max=5,
                    marks=slider_dates,
                    value=2,
                ),
            ],
            style={
                "margin-top": "2em",
                "margin-bottom": "2em",
                "padding-left": "2em",
                "padding-right": "2em"
            }
        ),

        dcc.Graph(
            id='message-timeline-graph',
            figure={
                'data': [
                    {
                        'y': [],
                        'x': [],
                        'type': 'scatter',
                        'name': 'SF'
                    },
                ],
                'layout': {
                    'title': 'Dash Data Visualization',
                    'xaxis': {
                        'title': 'Datetime'
                    },
                    'yaxis': {
                        'title': 'Number of Messages'
                    }
                }
            }
        ),
    ]
)


@DASH.callback(Output('discord-server-dropdown', 'options'),
               [Input('discord-server-dropdown', 'value')])
def set_discord_server_options(v):
    servers = list(db.session.query(Server.name, Server.id))
    if servers:
        return [{"label": "{} (id: {})".format(name, id), "value": id} for name, id in servers]
    else:
        return [{}]


@DASH.callback(Output('member-messages-graph', 'figure'),
               [Input('message-date-picker-range', 'start_date'),
                Input('message-date-picker-range', 'end_date'),
                Input("discord-server-dropdown", 'value')])
def update_graph_live(start_date, end_date, discord_server_id):
    messages = list(db.session.query(func.count(Message.id), Member.name)
                    .join(Member)
                    .join(Channel)
                    .join(Server)
                    .filter(
                        func.date(Message.timestamp) >= start_date,
                        func.date(Message.timestamp) <= end_date,
                        Server.id.in_(discord_server_id))
                    .group_by(Member.name))
    messages = sorted(messages, key=lambda tup: tup[0])
    messages.reverse()
    print(messages)
    return {
        'data': [
            {
                'y': [str(m[0]) for m in messages],
                'x': [m[1] for m in messages],
                'type': 'bar',
                'name': 'SF'
            },
        ],
        'layout': {
            'title': 'Messages per Member',
            'xaxis': {
                'title': 'Member'
            },
            'yaxis': {
                'title': 'Number of Messages'
            }
        },
    }


@DASH.callback(Output('message-timeline-graph', 'figure'),
               [Input('message-date-picker-range', 'start_date'),
                Input('message-date-picker-range', 'end_date'),
                Input("discord-server-dropdown", 'value'),
                Input("date-binning-slider", "value")
                ])
def update_timeline_messages(start_date, end_date, discord_server_id, bin):
    # TODO: integrate slider
    messages = list(db.session.query(func.count(Message.id), Message.timestamp)
                    .join(Channel)
                    .join(Server)
                    .filter(
                        func.date(Message.timestamp) >= start_date,
                        func.date(Message.timestamp) <= end_date,
                        Server.id.in_(discord_server_id))
                    .group_by(func.strftime(date_bins[bin], Message.timestamp)))
    return {
        'data': [
            {
                'y': [str(m[0]) for m in messages],
                'x': [m[1] for m in messages],
                'type': 'scatter',
                'name': 'SF',
                'mode': 'lines+markers'
            },
        ],
        'layout': {
            'title': 'Messages Timeline',
            'xaxis': {
                'title': 'Datetime'
            },
            'yaxis': {
                'title': 'Number of Messages'
            }
        },
    }


DASH.config.suppress_callback_exceptions = True
DASH.css.config.serve_locally = True
DASH.scripts.config.serve_locally = True


@APP.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    db.create_all()
    db.session.commit()
    return DASH.index()
