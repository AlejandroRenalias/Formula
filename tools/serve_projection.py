"""Serve the custom projection workspace and its canonical fixture on loopback."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse

ROOT = Path(__file__).resolve().parents[1]


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.split('?')[0] == '/fixture.json':
            self.path = '/tests/fixtures/projection_lap18.json'
        elif self.path.split('?')[0] in ('/', '/pitwall-concept.html'):
            self.path = '/design/pitwall-concept.html'
        elif self.path.startswith('/assets/'):
            self.path = '/design' + self.path
        super().do_GET()

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8502)
    args = parser.parse_args()
    with ThreadingHTTPServer(('127.0.0.1', args.port), partial(Handler, directory=str(ROOT))) as server:
        print(f'Formula: http://127.0.0.1:{args.port}/pitwall-concept.html', flush=True)
        server.serve_forever()
