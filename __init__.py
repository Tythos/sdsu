"""
"""

import os
import re
import csv
import ssl
from tornado import web, ioloop, httpserver, websocket

MOD_ROOT, _ = os.path.split(os.path.abspath(__file__))
STATIC_ROOT = MOD_ROOT + "/static" # users can change this module value
SECURITY_ROOT = MOD_ROOT + "/security" # user can change this module value
WSS_HANDLER_CLS = None
CREDENTIALER = []

class Credentialer(object):
    """Single-state repository of authentication and whitelisting methods.
    """

    def __init__(self):
        """Initialized against security credentials table. For now, this is
           fixed to */security/credentials.csv*.
        """
        with open(SECURITY_ROOT + "/credentials.csv", 'r') as f:
            dr = csv.DictReader(f)
            self.users = [row for row in dr]
            
    def verify(self, email, password):
        """Returns *True* if the given email/password pair satisfies a
           credentials entry. Stateless per request; single load at application
           initialization grabs credentials from .CSV table.
        """
        emails = [user["email"] for user in self.users]
        if email not in emails:
            return False
        user = self.users[emails.index(email)]
        if user["password"] != password:
            return False
        return True

    def assertWhitelist(self, userEmail, requestIp):
        """Returns *True* if the given user is whitelisted for access from the
           given IP. Whitelist satisfied if the given request IP falls within
           the whitelisted range (as parsed from a CIDR-style subnet mask). For
           example, a whitelisted IP of "10.10.15.10" with a range of 16 means
           any IP between 10.10.0.0 and 10.10.255.255 (i.e., only comparing the
           first 16 bits) is approved by the whitelist. Whitelist IP and range
           are stored in "whitelistMask" field of user credentials.
        """
        emails = [user["email"] for user in self.users]
        user = self.users[emails.index(userEmail)]
        parts = user["whitelistMask"].split("/")
        wlBits = Credentialer.ipToBits(parts[0])
        rqBits = Credentialer.ipToBits(requestIp)
        maskLength = int(parts[1])
        if Credentialer.isIPv4(parts[0]):
            maskLength += 16 # mask must also match 2002 prefix if converted
        matchBits = [wlBits[i] is rqBits[i] for i in range(maskLength)]
        if all(matchBits):
            return True
        return False

    @staticmethod
    def isIPv4(ip):
        """Returns *True* if the given string is a dotted quad (four integers
           seperated by a period).
        """
        return re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip) is not None

    @staticmethod
    def isIPv6(ip):
        """Returns *True* if the given string is a colon-delimited list of
           optional hexidecimal characters.
        """
        return re.match(r"^[\:\da-fA-F]+$", ip) is not None

    @staticmethod
    def ipToBits(ip):
        """Converts a dotted-quad string to bit (list of 128 bool values). If
           IP address has an IPv4 format, it is first converted to an IPv6
           (using 2002: prefix).
        """
        if Credentialer.isIPv4(ip):
            vals = list(map(int, ip.split(".")))
            ip = "2002:{:02x}{:02x}:{:02x}{:02x}::".format(*vals)
        bool128 = []
        if "::" in ip:
            left, right = ip.split("::")
            nLeft = len(left.split(":"))
            nRight = len(right.split(":"))
            middle = ["0000"] * (8 - nLeft - nRight)
            if len(left.strip()) is 0:
                left = "0000"
            if len(right.strip()) is 0:
                right = "0000"
            ip = ":".join([left] + middle + [right])
        for part in ip.split(":"):
            if len(part) < 4:
                part = "0" * (4 - len(part)) + part
            value = int(part, 16)
            bits = "{0:016b}".format(value)
            bool128 = bool128 + [b == "1" for b in bits]
        return bool128

class BaseHandler(web.RequestHandler):
    """Unifying handler model to ensure uniform user access for authenticated
       and login methods.
    """

    def get_current_user(self):
        """Overrides default user retrieval to return email from secure session
           cookie. Utilized by subclasses with authentication methods.
        """
        return self.get_secure_cookie("user")

class IndexHandler(BaseHandler):
    """Default router to index (authenticated).
    """

    @web.authenticated
    def get(self):
        """Authenticated method for retrieving index page. Not cached.
        """
        with open(STATIC_ROOT + "/index.html", 'r') as f:
            self.write(f.read())

class WssHandler(websocket.WebSocketHandler, BaseHandler):
    """Secure WebSocket handler. Open method is authenticated. To be extended
       by specific message handling behaviors. Scope is single-client
       connection.
    """

    @web.authenticated
    def open(self):
        """Invoked when secure WebSocket is opened. Authenticated. Forwards to
           method *on_open()* for more consistent method naming.
        """
        self.on_open()

    def on_open(self):
        """Mirrors (invoked by) *open()* for more consistent method naming by
           user subclasses.
        """
        print("WebSocket opened")

    def on_message(self, message):
        """Invoked when a message is received from the client.
        """
        self.write_message(u"You said: " + message)

    def on_close(self):
        """Invoked when a WebSocket connection with the client is closed.
        """
        print("WebSocket closed")

class SplashHandler(BaseHandler):
    """Unique non-authenticated handler to manage splash page retrieval and
       login behaviors.
    """

    def get(self, *args):
        """Clears login if a user exists (effectively login and logout are same
           resource). Returns the splash page.
        """
        if self.get_current_user() is not None:
            self.clear_cookie("user")
        with open(STATIC_ROOT + "/splash.html", 'r') as f:
            self.write(f.read())

    def post(self, *args):
        """Processes login request (form submission from splash page). If
           successful, redirects to root (index) handler. Otherwise, redirects
           to self (splash) with error tag in fragment.
        """
        email = self.get_argument("email")
        password = self.get_argument("password")
        address = re.sub(r"\%.+$", "", self.request.remote_ip)
        if CREDENTIALER.verify(email, password) and CREDENTIALER.assertWhitelist(email, address):
            self.set_secure_cookie("user", email)
            self.redirect("/")
        else:
            self.redirect("/splash#error")

class AuthStaticHandler(web.StaticFileHandler, BaseHandler):
    """Subclasses both static file handling and base handler (for
       authentication) behaviors.
    """

    def __init__(self, application, request, **kwargs):
        """Initializes with static path for this package. Since BaseHandler
           only subclasses web.RequestHandler (common to both inheritance
           trees), we only need to invoke the StaticFileHandler constructor.
        """
        web.StaticFileHandler.__init__(self, application, request, path=STATIC_ROOT, **kwargs)
    
    @web.authenticated
    def get(self, *args, **kwargs):
        """Authenticated method for static file retrieval. Invokes parent get()
           after decorating with authentication.
        """
        return web.StaticFileHandler.get(self, *args, **kwargs)

def getSslCtx():
    """Generates a new SSL context based on the certificate and key files in
       the package's */security* subdirectory.
    """
    certPath = SECURITY_ROOT + "/certificate.pem"
    keyPath = SECURITY_ROOT + "/key.pem"
    ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ctx.load_cert_chain(certPath, keyPath)
    return ctx

def main(staticRoot=None, securityRoot=None, wssHandlerCls=None):
    """Constructs a singleton credentialer, then initializes the application
       with this module's handlers. By default, this uses the built-in 
       WssHandler, but an extended class can be provided instead for
       customization of message handling. Listens on 443 after wrapping with
       the SSL context defined in *getSslCtx()*.
    """
    global CREDENTIALER, STATIC_ROOT, SECURITY_ROOT, WSS_HANDLER_CLS
    if staticRoot is not None:
        STATIC_ROOT = staticRoot
    if securityRoot is not None:
        SECURITY_ROOT = securityRoot
    if wssHandlerCls is not None:
        WSS_HANDLER_CLS = wssHandlerCls
    if WSS_HANDLER_CLS is None:
        WSS_HANDLER_CLS = WssHandler
    CREDENTIALER = Credentialer()
    settings = {
        "static_path": STATIC_ROOT,
        "cookie_secret": "nanxuan subverse virginiasr gclark worklab".replace(" ", "_").upper(),
        "login_url": "/splash"
    }
    app = web.Application([
        (r"/splash(#.+)?$", SplashHandler),
        (r"/$", IndexHandler),
        (r"/wss$", WSS_HANDLER_CLS),
        (r"/(.+)", AuthStaticHandler)
    ], **settings)
    ctx = getSslCtx()
    server = httpserver.HTTPServer(app, ssl_options=ctx)
    server.listen(443)
    try:
        ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        ioloop.IOLoop.instance().stop()

if __name__ == "__main__":
    main()
