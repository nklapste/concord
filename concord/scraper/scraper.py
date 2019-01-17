# -*- coding: utf-8 -*-

from logging import getLogger

from discord.client import Forbidden, NotFound, HTTPException

# from concord.nlp_dev import get_doc_entity
from concord.scraper.utils import run_discord_sync

__log__ = getLogger(__name__)

with open('token.txt') as f:
    token = f.read().strip()


@run_discord_sync(token=token, timeout=None, bot=False)
async def iter_server_messages_v2(client, db, limit: int = 10):
    from concord.server.server import Server, Member, Channel, Message

    def get_or_create(session, model, **kwargs):
        instance = session.query(model).filter_by(**kwargs).first()
        if instance:
            return instance
        else:
            instance = model(**kwargs)
            session.add(instance)
            session.commit()
            return instance

    for server in client.servers:
        server = server
        db_server = get_or_create(
            db.session,
            Server,
            id=server.id,
            name=server.name
        )
        for channel in server.channels:
            channel = channel
            db_channel = get_or_create(
                db.session,
                Channel,
                name=channel.name,
                id=channel.id,
                server=server.id
            )

            try:
                async for message in client.logs_from(channel, limit=limit):
                    message = message
                    __log__.info('checking message {}'.format(message.content))
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
                        # channel_id=channel.id,
                        content=message.content,
                        timestamp=message.timestamp,
                    )
                    for mentioned_member in message.mentions:
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
            except Forbidden:  # cant access channel
                pass
            except NotFound:  # cant find channel
                pass
            except HTTPException:  # discord likely down
                pass
