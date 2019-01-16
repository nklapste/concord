# -*- coding: utf-8 -*-

"""Represent the servers/messages/members that a Discord token can access
as simple SQL database"""

import datetime

from pony.orm import Database, PrimaryKey, Required, Set, Optional

db = Database()


class Member(db.Entity):
    id = PrimaryKey(str)
    name = Required(str)
    messages = Set("Message", reverse="author")
    mentions = Set("Message", reverse="mentions")


class Server(db.Entity):
    id = PrimaryKey(str)
    name = Required(str)
    channels = Set("Channel")


class Channel(db.Entity):
    id = PrimaryKey(str)
    name = Required(str)
    server = Required(Server)
    messages = Set("Message", reverse="channel")


class Message(db.Entity):
    id = Required(str)
    author = Required(Member)
    timestamp = Required(datetime.datetime)
    type = Required(int)
    content = Optional(str)
    channel = Optional(Channel)
    mentions = Set("Member", reverse="mentions")
    attributes = Optional(str)
    PrimaryKey(id, type)


def get_or_create(model, defaults=None, **params):
    """Get an item from the database if it does not exist add it to the
    database using the provided default

    :param model:
    :type model: Type[db.Entity]

    :param defaults: dictionary of default keys/values to use to create a
        new database item (only used if the item does not exist in
        the database)
    :type defaults: dict

    :param params: kwargs used to select the item from the database

    :return: model that was either obtained from the database or newly created
        and added to the database
    :rtype: Type[db.Entity]
    """
    if defaults is None:
        defaults = {}
    obj = model.get(**params)
    if obj is None:
        params = params.copy()
        for k, v in defaults.items():
            if k not in params:
                params[k] = v
        return model(**params)
    else:
        return obj
