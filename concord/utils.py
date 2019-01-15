# -*- coding: utf-8 -*-

"""Utilities and misc functions for concord"""

import asyncio

from discord import Client


class SyncDiscordResult(object):
    def __init__(self):
        self.result = None
        self.timed_out = False
        self.exception = None


def run_discord_sync(token: str, timeout: float = None, bot: bool = True):
    def run_discord_sync_wrapper(func):
        def func_wrapper(*args, **kwargs):
            loop = asyncio.new_event_loop()
            client = Client(is_bot=bot, loop=loop)
            sync_discord_result = SyncDiscordResult()

            @client.event
            async def on_ready():
                try:
                    sync_discord_result.result = await func(client, *args, **kwargs)
                except Exception as error:
                    sync_discord_result.exception = error
                client.close()
                loop.call_soon_threadsafe(loop.stop)

            loop.run_until_complete(client.login(token, bot=bot))
            try:
                loop.run_until_complete(
                    asyncio.wait_for(client.connect(), timeout=timeout, loop=loop))
            except asyncio.TimeoutError:
                sync_discord_result.timed_out = True
            except RuntimeError as e:
                if "Event loop stopped before Future completed" not in str(e):
                    raise
            loop.close()

            if sync_discord_result.timed_out:
                import logging
                logging.error("function {} timed out after {} seconds".format(func, timeout))
            if sync_discord_result.exception is not None:
                raise sync_discord_result.exception
            return sync_discord_result.result
        return func_wrapper
    return run_discord_sync_wrapper
