from discord import Message, Channel, Server
from discord.client import Forbidden, NotFound, HTTPException
from pony.orm import db_session

from concord.database import db, DBMember, DBServer, DBChannel, DBMessage, \
    get_or_create
from concord.utils import run_discord_sync


with open('..\\token.txt') as f:
    token = f.read().strip()


@db_session
@run_discord_sync(token=token, timeout=None, bot=False)
async def iter_server_messages(client, limit: int = 10):
    for server in client.servers:
        server: Server = server
        ser = get_or_create(DBServer, id=server.id, name=server.name)
        for channel in server.channels:
            channel: Channel = channel
            chan = get_or_create(
                DBChannel,
                name=channel.name,
                id=channel.id,
                server=ser
            )

            try:
                async for message in client.logs_from(channel, limit=limit):
                    message: Message = message
                    mem = get_or_create(DBMember, id=message.author.id, name=message.author.name)
                    mes = get_or_create(
                        DBMessage,
                        author=mem,
                        channel=chan,
                        content=message.content,
                        timestamp=message.timestamp,
                    )
                    for mentioned_member in message.mentions:
                        mem = get_or_create(DBMember, id=mentioned_member.id, name=mentioned_member.name)
                        mes.mentions.add(mem)
            except Forbidden:  # cant access channel
                pass
            except NotFound:  # cant find channel
                pass
            except HTTPException:  # discord likely down
                pass


# TODO: dev testing
db.bind(provider='sqlite', filename='database.sqlite', create_db=True)
db.generate_mapping(create_tables=True)
iter_server_messages(1000)
