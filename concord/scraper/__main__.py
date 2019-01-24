#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""argparse and main entrypoint script for the concord Discord scraper bot"""

import argparse
import sys

from concord.common import add_log_parser, init_logging
from concord.scraper.bot import client, background_scrape_messages
from concord.server.server import APP, DEFAULT_SQLITE_PATH


def get_parser() -> argparse.ArgumentParser:
    """Create and return the argparser for concord Discord scraper"""
    parser = argparse.ArgumentParser(
        description="Start the concord Discord scraper bot",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("-s", "--self-bot", dest="self_bot",
                        action="store_true",
                        help="Enable running the scraper as a self bot")
    parser.add_argument("-w", "--scrape-wait", dest="scrape_wait",
                        type=int, default=60,
                        help="Time in seconds to wait between scrape "
                             "executions")
    parser.add_argument("-l", "--messages-limit", dest="messages_limit",
                        type=int, default=100,
                        help="The maximum number of messages to scrape from "
                             "each discord channel")
    parser.add_argument("-tf", "--token-file", dest="token_file",
                        required=True,
                        help="Path to file containing the Discord token for "
                             "the bot")
    parser.add_argument("--database", default=DEFAULT_SQLITE_PATH,
                        help="Path to the SQLITE database to store messages")

    add_log_parser(parser)

    return parser


def main(argv=sys.argv[1:]) -> int:
    """main entry point for the concord Discord scraper bot"""
    parser = get_parser()
    args = parser.parse_args(argv)

    init_logging(args, "concord_bot.log")
    with open(args.token_file, "r") as f:
        token = f.read().strip()

    APP.config['SQLALCHEMY_DATABASE_URI'] = args.database

    client.loop.create_task(
        background_scrape_messages(args.scrape_wait, args.messages_limit))
    client.run(token, bot=not args.self_bot)

    return 0


if __name__ == "__main__":
    sys.exit(main())
