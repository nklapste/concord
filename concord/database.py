# -*- coding: utf-8 -*-

"""Represent the servers/messages/members that a Discord token can access
as simple SQL database"""
import datetime

from pony.orm import Database, PrimaryKey, Required, Set, Optional

db = Database()


class DBMember(db.Entity):
    id = PrimaryKey(str)
    name = Required(str)
    messages = Set("DBMessage", reverse="author")
    mentions = Set("DBMessage", reverse="mentions")


class DBServer(db.Entity):
    id = PrimaryKey(str)
    name = Required(str)
    channels = Set("DBChannel")


class DBChannel(db.Entity):
    id = PrimaryKey(str)
    name = Required(str)
    server = Required(DBServer)
    messages = Set("DBMessage", reverse="channel")


class DBMessage(db.Entity):
    author = Required(DBMember)
    content = Optional(str)
    timestamp = Required(datetime.datetime)
    channel = Optional(DBChannel)
    mentions = Set("DBMember", reverse="mentions")


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
