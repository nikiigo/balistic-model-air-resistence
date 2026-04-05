from __future__ import annotations

import argparse
from wsgiref.simple_server import make_server

from ballistics.web.app import create_application
from ballistics.web.templates import HTML_PAGE

application = create_application(HTML_PAGE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the interactive ballistics simulator.")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind.")
    parser.add_argument("--port", type=int, default=8000, help="Port to serve on.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with make_server(args.host, args.port, application) as server:
        print(f"Serving ballistics simulator at http://{args.host}:{args.port}")
        server.serve_forever()


if __name__ == "__main__":
    main()
