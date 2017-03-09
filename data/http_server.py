import time
import os

from BaseHTTPServer   import BaseHTTPRequestHandler, HTTPServer
from SocketServer     import ThreadingMixIn

from urlparse import urlparse, parse_qs
import json
from random import choice as random_choice
from string import ascii_uppercase, digits

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
	pass


HOST_NAME   = os.getenv("CROP_HTTP_HOST", '127.0.0.1')
PORT_NUMBER = int(os.getenv("CROP_HTTP_PORT", 9000))


class CropHandler(BaseHTTPRequestHandler):
	def log_message(self, fmt, *args):
		fmt = "[{}] {}".format(self.unique_id, fmt)
		BaseHTTPRequestHandler.log_message(self, fmt, *args)

	def do_PUT(self):
		"""Respond to a PUT request."""
		try:
			self.set_unique_request_id()
			params = self.get_query_params()
			self.log_message("parsed query params: %s; gonna read body", params) # log example
			body   = self.read_request_body()
			self.reply_success(params, body)
		except Exception as e: 
			self.reply_fail(e)

	def read_request_body(self):
		content_len = int(self.headers.getheader('content-length', 0))
		self.rfile._sock.settimeout(5) # throw timeout exception if no content read after 5 seconds
		body = self.rfile.read(content_len)
		return body

	def get_query_params(self):
		params = {}
		query_components = parse_qs(urlparse(self.path).query)
		ident = query_components.get("ident",[])
		if len(ident) > 0 and len(ident[0]) > 0:
			params["ident"] = ident[0] if ident[0].startswith("id") else "id"+ident[0]
		else:
			raise ValueError("ident required") 
		return params

	def reply_success(self,params,body):
		self.send_response(200)
		self.send_header("Content-type", "application/json")
		self.end_headers()
		response = {
			"ident": params.get("ident","<none>"),
			"body": body,
			"face_count" : 0,
		}
		self.wfile.write(json.dumps(response))

	def reply_fail(self, err):
		self.send_response(500)
		self.send_header("Content-type", "application/json")
		self.end_headers()
		response = {"error": "{}".format(err)}

		self.wfile.write(json.dumps(response))
	def set_unique_request_id(self):
		self.unique_id = ''.join(random_choice(ascii_uppercase + digits) for _ in range(10))
		

if __name__ == '__main__':
	server_class = ThreadedHTTPServer
	httpd = server_class((HOST_NAME, PORT_NUMBER), CropHandler)
	print time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER)
	try:
		httpd.serve_forever()
	except KeyboardInterrupt:
		pass
	httpd.server_close()
	print time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER)
