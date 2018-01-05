
import model
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

# initialize csv reading interval as 100
myModel = model.DataModel(100)

class Server():
    def __init__(self):
        self.run(HTTPServer, simpleHandler)
        
    def run(self, server_class=HTTPServer, handler_class=BaseHTTPRequestHandler):
        server_address = ('127.0.0.1', 8000)
        server = server_class(server_address, handler_class)
        server.serve_forever()
        
class simpleHandler(BaseHTTPRequestHandler):

    def _set_headers(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_GET(self):
        url = urlparse(self.path)
        queries = parse_qs(url.query)
        content = False
        print('url:', url)
        print('path:', self.path)
        print('url.path: ', url.path)
        
        if url.path == '/dayinfo':
            content = myModel.getDayInfo()
        
        if url.path == '/popular':
            print(queries['time'][0])
            content = myModel.getPopularDevices(queries['time'][0])
        
        if url.path == '/selects':
            content = myModel.getSelectInfo()
        
        if url.path == '/recent':
            payload = {
                'type': queries['type'][0],
                'connection': queries['connection'][0]
            }
            content = myModel.getRecentInfo(payload)
        
        if content == False:
            return self.res_not_found()
        return self.res_json(content)

    
    def res_json(self, content):
        print('working')
        self._set_headers()
        self.end_headers()
        print('content:', content)
        jsonStr = json.dumps(content, ensure_ascii=False).encode('utf8')
        self.wfile.write(jsonStr)
        return
    
    def res_not_found(self):
        self.send_response(404)
        self.end_headers()
        return

                

    
                        
        
myServer = Server()
