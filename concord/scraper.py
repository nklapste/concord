# -*- coding: utf-8 -*-

from logging import getLogger
from discord import Message, Channel, Server, MessageType
from discord.client import Forbidden, NotFound, HTTPException
from pony.orm import db_session

from concord.database import Member as DBMember, Server as DBServer, \
    Channel as DBChannel, Message as DBMessage, get_or_create, db
from concord.nlp_dev import get_doc_entity

from concord.utils import run_discord_sync


__log__ = getLogger(__name__)


with open('..\\token.txt') as f:
    token = f.read().strip()


@db_session
@run_discord_sync(token=token, timeout=None, bot=False)
async def iter_server_messages(client, limit: int = 10):
    for server in client.servers:
        server: Server = server
        db_server = get_or_create(
            DBServer,
            id=server.id,
            name=server.name
        )
        for channel in server.channels:
            channel: Channel = channel
            db_channel = get_or_create(
                DBChannel,
                name=channel.name,
                id=channel.id,
                server=db_server
            )
            try:
                async for message in client.logs_from(channel, limit=limit):
                    message: Message = message
                    __log__.info('checking message {}'.format(message.content))
                    db_member = get_or_create(
                        DBMember,
                        id=message.author.id,
                        name=message.author.name
                    )
                    db_message = get_or_create(
                        DBMessage,
                        id=message.id,
                        author=db_member,
                        channel=db_channel,
                        type=message.type.value if isinstance(message.type, MessageType) else message.type,
                        content=message.content,
                        attributes=str(sorted(list(get_doc_entity(str(message.content))))),
                        timestamp=message.timestamp,
                    )
                    for mentioned_member in message.mentions:
                        db_member = get_or_create(
                            DBMember,
                            id=mentioned_member.id,
                            name=mentioned_member.name
                        )
                        db_message.mentions.add(db_member)
                    # TODO: enable when discordpy hits 1.0.0
                    # for reactions in message.reactions:
                    #     for reacting_member in reactions.users():
                    #         pass
            except Forbidden:  # cant access channel
                pass
            except NotFound:  # cant find channel
                pass
            except HTTPException:  # discord likely down
                pass


# TODO: dev testing
db.bind(provider='sqlite', filename='database.sqlite', create_db=True)
db.generate_mapping(create_tables=True)
iter_server_messages(200)
