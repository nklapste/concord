#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""main entrypoint for the concord server"""

import argparse
import sys
from logging import getLogger

from cheroot.wsgi import Server as WSGIServer, PathInfoDispatcher

from concord.common import add_log_parser
from concord.server.server import APP

__log__ = getLogger(__name__)


def get_parser() -> argparse.ArgumentParser:
    """Create and return the argparser for concord flask/cheroot server"""
    parser = argparse.ArgumentParser(
        description="Start the concord flask/cheroot server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    group = parser.add_argument_group("server")
    group.add_argument("-d", "--host", default='localhost',
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

    __log__.info("starting server: host: {} port: {}".format(args.host, args.port))

    if args.debug:
        APP.run(
            host=args.host,
            port=args.port,
            debug=True
        )
    else:
        path_info_dispatcher = PathInfoDispatcher({'/': APP})
        server = WSGIServer((args.host, args.port), path_info_dispatcher)
        try:
            server.start()
        except KeyboardInterrupt:
            __log__.info("stopping server: KeyboardInterrupt detected")
            server.stop()
            return 0
        except Exception:
            __log__.exception("stopping server: unexpected exception")
            raise


if __name__ == "__main__":
    sys.exit(main())
