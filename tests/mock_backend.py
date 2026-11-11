#!/usr/bin/env python3
import json
from http.server import BaseHTTPRequestHandler,HTTPServer
from urllib.parse import urlsplit
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path=urlsplit(self.path).path
        if path=='/api/opensky':
            data={'time':123,'states':[['abc123','FIXTURE','Testland',None,None,2.3,48.8,5000,False,145,90]]}
        elif path=='/api/regional-brief':
            data={'status':'fixture','articles':[{'title':'Synthetic test'}]}
        elif path=='/api/weather-effects':
            data={'status':'fixture','weather':'simulated'}
        else:data={'status':'fixture','source':path}
        body=json.dumps(data).encode('utf8')
        self.send_response(200)
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self,*args):pass
HTTPServer(('127.0.0.1',4173),Handler).serve_forever()
