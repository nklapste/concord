#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""main entrypoint for the concord server"""

import argparse
import sys
from logging import getLogger

from concord.common import add_log_parser

__log__ = getLogger(__name__)


def get_parser() -> argparse.ArgumentParser:
    """Create and return the argparser for concord flask/cheroot server"""
    parser = argparse.ArgumentParser(
        description="Start the concord flask/cheroot server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    group = parser.add_argument_group("server")
    group.add_argument("-d", "--host", default='0.0.0.0',
                       help="Hostname to listen on")
    group.add_argument("-p", "--port", default=8080, type=int,
                       help="Port of the webserver")
    group.add_argument("--debug", action="store_true",
                       help="Run the server in Flask debug mode")
    add_log_parser(parser)

    return parser


def main(argv=sys.argv[1:]) -> int:
    parser = get_parser()
    args = parser.parse_args(argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
