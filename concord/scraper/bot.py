# -*- coding: utf-8 -*-

"""A Discord bot for scraping messages and storing them into a sql database

TODO: need to move to a better databasing solution at some point
"""

import asyncio
import datetime
from logging import getLogger
from typing import Optional

from discord import NotFound, HTTPException, Forbidden, Client

from concord.server.server import db, Server, Member, Channel, Message

client = Client()

__log__ = getLogger(__name__)


# TODO: need some helper to keep database trimmed to only that latest 10,000 records or such


def get_latest_stored_message(channel) -> Optional[datetime.datetime]:
    latest_stored_message =\
        db.session.query(Message)\
                  .filter(Message.channel == channel)\
                  .order_by(Message.timestamp.desc())\
                  .first()
    if latest_stored_message:
        return latest_stored_message.timestamp
    return None


def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance


async def scrape_messages(limit: int):
    for server in client.servers:
        server = server
        __log__.debug("obtained server: {}".format(server.id))
        db_server = get_or_create(
            db.session,
            Server,
            id=server.id,
            name=server.name
        )
        for channel in server.channels:
            __log__.debug("obtained channel: {}".format(channel.id))
            channel = channel
            db_channel = get_or_create(
                db.session,
                Channel,
                name=channel.name,
                id=channel.id,
                server=server.id
            )
            latest_stored_message_datetime = get_latest_stored_message(db_channel)
            try:
                async for message in client.logs_from(channel, after=latest_stored_message_datetime, limit=limit):
                    __log__.debug("obtained message: {} author: {}".format(
                        message.id, message.author.id))
                    message = message
                    db_member = get_or_create(
                        db.session,
                        Member,
                        id=message.author.id,
                        name=message.author.name
                    )
                    db_message = get_or_create(
                        db.session,
                        Message,
                        id=message.id,
                        author=message.author.id,
                        channel=db_channel,
                        content=message.content,
                        timestamp=message.timestamp,
                    )
                    for mentioned_member in message.mentions:
                        __log__.debug("obtained mention: {}".format(
                            mentioned_member.id))
                        db_member = get_or_create(
                            db.session,
                            Member,
                            id=mentioned_member.id,
                            name=mentioned_member.name
                        )
                    # TODO: enable when discordpy hits 1.0.0
                    # for reactions in message.reactions:
                    #     for reacting_member in reactions.users():
                    #         pass
            except Forbidden:
                pass
            except NotFound:
                pass
            except HTTPException:
                pass


async def background_scrape_messages(scrape_wait: int, limit: int):
    """Scrape the messages of all available servers"""
    await client.wait_until_ready()
    while not client.is_closed:
        db.create_all()
        db.session.commit()
        await scrape_messages(limit)
        await asyncio.sleep(scrape_wait)


@client.event
async def on_ready():
    __log__.info("logged in as: {}".format(client.user.id))
