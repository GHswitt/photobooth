'''
Created Sep, 2015

Licence: GNU AGPL

@author: Sebastian Witt
'''

import SimpleHTTPServer
import SocketServer
import threading
import select

class pbHTTPHandler (SimpleHTTPServer.SimpleHTTPRequestHandler):
  def do_HEAD(s):
    s.send_response (200)
    if s.path == '/screen':
      s.send_header ("Content-type", "image/jpeg")
    else:
      s.send_header ("Content-type", "text/plain")
    s.send_header ("refresh", "10")
    s.end_headers ()
    
  def do_GET(s):
    s.do_HEAD()
    if s.path == '/screen':
      # Screenshot
      try:
	f = open ('screen.jpg', 'rb')
	s.wfile.write (f.read ())
	f.close ()
      except:
	return
    else:
      # Logfile
      limit = 5000
      try:
	f = open ('pb.log', 'r')
	f.seek (0, 2)
	size = f.tell ()
	if (size > limit):
	  f.seek (-limit, 2)
	else:
	  f.seek (0, 0)
	s.wfile.write (f.read (limit))
	f.close ()
      except:
	return
    
class pbWeb (threading.Thread):
  def __init__ (self):
    super (pbWeb, self).__init__()
    # Event for stopping this webserver
    self._stop = threading.Event ()

  def stop (self):
    self._stop.set ()

  def isStopped (self):
    return self._stop.isSet ()
  
  def run (self):
    # TCPServer with HTTP handler
    httpd = SocketServer.TCPServer (("", 8080), pbHTTPHandler)

    # Run until stopped
    while not self.isStopped ():
      # Wait for request, timeout after 3s
      r,w,x = select.select ([httpd.socket], [], [], 3)
      # Check for request
      if r:
	httpd.handle_request ()
