#!/usr/bin/env python3
"""Static server for glimmer-a. E2E_3D0=1 → /index.html without 3d= redirects to ?3d=0&… so legacy e2e keep 2D."""
import os, sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8510
ROOT = sys.argv[2] if len(sys.argv) > 2 else os.getcwd()
FORCE_3D0 = os.environ.get('E2E_3D0') == '1'

class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)
    def do_GET(self):
        u = urlparse(self.path)
        if FORCE_3D0 and (u.path == '/' or u.path == '/index.html' or u.path.endswith('/index.html')):
            qs = parse_qs(u.query, keep_blank_values=True)
            if '3d' not in qs:
                loc = '/index.html?3d=0'
                if u.query:
                    loc += '&' + u.query
                self.send_response(302)
                self.send_header('Location', loc)
                self.end_headers()
                return
        return super().do_GET()
    def log_message(self, fmt, *args):
        if os.environ.get('HTTP_VERBOSE'):
            super().log_message(fmt, *args)

if __name__ == '__main__':
    os.chdir(ROOT)
    httpd = ThreadingHTTPServer(('0.0.0.0', PORT), H)
    print('serve %s on %s  E2E_3D0=%s' % (ROOT, PORT, FORCE_3D0), flush=True)
    httpd.serve_forever()
