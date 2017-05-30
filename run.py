#!/usr/bin/python
import sys
import logging

from app import app

log = logging.getLogger(__name__)

def run():
    mode = '-p'
    try:
        mode = sys.argv[1]
    except IndexError:
        pass

    if mode == "-p" or mode == "--prod":
        log.info(' * Production Environment *')
        app.run(debug=True, host='0.0.0.0')

    elif mode == "-d" or mode == "--dev":
        log.info(' * Development Environment *')
        app.run(debug=True)

    else:
        raise ValueError("Unrecognised command argument: '{}'. Use --dev or --prod".format(mode))


if __name__ == '__main__':
    logging.basicConfig(
        level= 0,
        format= '%(message)s',
        datefmt="%H:%M"
    )

    run()
