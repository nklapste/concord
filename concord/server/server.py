#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Flask server definition

TODO: implement
"""

from logging import getLogger
from threading import Thread

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from flask import Flask, render_template
from flask_restplus import Api, reqparse, Resource, fields
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

from concord import __version__
from concord.scraper.scraper import iter_server_messages_v2

__log__ = getLogger(__name__)

APP = Flask(__name__)
APP.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
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
    server = db.Column(db.String(80), db.ForeignKey('server.id'), nullable=False)


class Message(db.Model):
    id = db.Column(db.String(80), primary_key=True)
    author = db.Column(db.String(80), db.ForeignKey('member.id'), nullable=False)
    timestamp = db.Column(db.DateTime)
    channel_id = db.Column(db.String(80), db.ForeignKey('channel.id'), nullable=False)
    channel = db.relationship('Channel', backref='channel_messages', lazy=True)
    content = db.Column(db.UnicodeText(), nullable=True)


##################
# main frontend
##################


@APP.route('/', methods=["GET"])
def index():
    # parse request arguments
    return render_template('index.html')


##################
# dash frontend
##################


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

DASH = dash.Dash(__name__, server=APP, external_stylesheets=external_stylesheets)


DASH.layout = html.Div(
    children=[
        html.H1(children='Concord'),
        html.Div(children='Visualize Your Discord Server'),
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
        dcc.Interval(
            id='interval-component',
            interval=10 * 1000,  # in milliseconds
            n_intervals=0
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
        dcc.Interval(
            id='interval-message-timeline-graph',
            interval=10 * 1000,  # in milliseconds
            n_intervals=0
        ),
    ]
)


@DASH.callback(Output('member-messages-graph', 'figure'),
              [Input('interval-component', 'n_intervals')])
def update_graph_live(n):
    messages = list(db.session.query(func.count(Message.id), Member.name).join(Member).group_by(Member.name))
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


@APP.route('/dashboard', methods=['GET', 'POST'])
def dasboard():
    db.create_all()
    db.session.commit()
    return DASH.index()


@DASH.callback(Output('message-timeline-graph', 'figure'),
              [Input('interval-message-timeline-graph', 'n_intervals')])
def update_timeline_messages(n):
    messages = \
        list(db.session.query(func.count(Message.id), Message.timestamp)
             .group_by(func.strftime("%Y-%m-%d-%H:00:00.000", Message.timestamp)))
    return {
    'data': [
        {
            'y': [str(m[0]) for m in messages],
            'x': [m[1] for m in messages],
            'type': 'scatter',
            'name': 'SF'
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


##################
# api backend
##################


API = Api(
    APP,
    version="{}.{}.{}".format(*__version__),
    title='Concord API',
    doc='/api/doc',
)

connections_parser = reqparse.RequestParser()
connections_parser.add_argument('token', type=str, help='User Discord token')
connections_parser.add_argument('server_name', type=str,
                                help="Name of the Discord server to collect "
                                     "messages from")
connections_parser.add_argument('messages_number', type=int,
                                default=30,
                                help="Number of Discord messages to collect")
connections_parser.add_argument('timeout', type=float,
                                default=30,
                                help="Time to collect Discord messages before "
                                     "stopping")


graph_url_model = API.model('graphURL', {"graphURL": fields.String})


@API.route('/api/login')
@API.expect(connections_parser)
class GetConnectionsGraph(Resource):
    @API.marshal_with(graph_url_model, code=201, description='Object created')
    def post(self):
        args = connections_parser.parse_args()
        db.create_all()
        # TODO: init custom db for each token
        t = Thread(target=iter_server_messages_v2, args=[db, 100], daemon=True)
        t.start()
        return {"graphURL": "/dash"}, 201


if __name__ == '__main__':
    APP.run(host='localhost', port=8080, debug=True)
