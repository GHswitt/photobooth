'''
Created Sep, 2015

Licence: GNU AGPL

@author: Sebastian Witt
'''

import SimpleHTTPServer
import SocketServer
import threading
import select

#class pbServer(SocketServer.ThreadingTCPServer):
class pbServer(SocketServer.TCPServer):
  def __init__(self, server_address, RequestHandlerClass, GetImageFunction):
    SocketServer.TCPServer.__init__(self, 
                                    server_address, 
                                    RequestHandlerClass)
    self.GetImage = GetImageFunction
        
class pbHTTPHandler (SimpleHTTPServer.SimpleHTTPRequestHandler):
  # Handle header
  def do_HEAD(s):
    # Ignore favicon.ico
    if s.path == '/favicon.ico':
      s.send_response (404)
      s.end_headers ()
      return
    
    s.send_response (200)
    
    if s.path == '/log':
      s.send_header ("Content-type", "text/plain")
    elif s.path.split ('?', 1)[0] == '/current.jpg':
      s.send_header ("Content-type", "image/jpeg")
      s.send_header ("refresh", "10")
    else:
      s.send_header ("Content-type", "text/html")

    s.end_headers ()

  # Handle GET
  def do_GET(s):
    s.do_HEAD()
    try:
      if s.path == '/log':
        # Logfile
        limit = 5000
        f = open ('pb.log', 'r')
        f.seek (0, 2)
        size = f.tell ()
        if (size > limit):
          f.seek (-limit, 2)
        else:
          f.seek (0, 0)
        s.wfile.write (f.read (limit))
        f.close ()
      elif s.path.split ('?', 1)[0] == '/current.jpg':
        # Current image
        s.wfile.write (s.server.GetImage ())
      else:
        f = open ('index.html', 'r')
        s.wfile.write (f.read ())
        f.close ()
    except:
      return

class pbWeb (threading.Thread):
  def __init__ (self, GetImageFunction):
    super (pbWeb, self).__init__()
    # Event for stopping this webserver
    self._stop = threading.Event ()
    self.GetImage = GetImageFunction

  def stop (self):
    self._stop.set ()

  def isStopped (self):
    return self._stop.isSet ()
  
  def run (self):
    # TCPServer with HTTP handler
    httpd = pbServer (("", 8080), pbHTTPHandler, self.GetImage)

    # Run until stopped
    while not self.isStopped ():
      # Wait for request, timeout after 3s
      r,w,x = select.select ([httpd.socket], [], [], 3)
      # Check for request
      if r:
        httpd.handle_request ()
