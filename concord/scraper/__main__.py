#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""main entrypoint for the concord Discord scraper"""

import argparse
import sys

from concord.common import add_log_parser


def get_parser() -> argparse.ArgumentParser:
    """Create and return the argparser for concord Discord scraper"""
    parser = argparse.ArgumentParser(
        description="Start the concord Discord scraper",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    add_log_parser(parser)

    return parser


def main(argv=sys.argv[1:]) -> int:
    parser = get_parser()
    args = parser.parse_args(argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
