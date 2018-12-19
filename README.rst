SDSU
====

*Skim milk. Gummy bears. Pure genius.*

.. contents::

Quick Start
-----------

.. code::

 > python -c "import sdsu; sdsu.main()"

Overview
--------

The Secure, Dual-use Server Usage provides:

* A preconfigured, multi-handler Tornado web server
 
* Static file hosting from the */static* subdirectory

* SSL encryption using the certificates stored in */security*

* Login protection (including address whitelisting) from the credentials in
  */security*

* Secure WebSocket exchange on the same port service as static file hosting,
  using the */wss* path.

The *sdsu.main()* method takes three parameters that allow users to customize
the configuration of a SDSU server before it launches.

securityRoot
------------

The */security* subdirectory contains three files:

* *certificate.pem* defines the server's SSL certificate

* *credentials.csv* defines the user table. Each user is defined by an email
  address ("email"), password ("password"), and whitelist mask (CIDR-style,
  IPv6 preferred but IPv4 will be translated automatically with a "2002:"
  prefix.) Password and whitelist mask will be used by the SplasHandler.post()
  method when verifying credential submissions.

* *key.pem*, the server's private SSL key.

Users can customize security configurations by creating a new copy of this
directory, modifying it's contents, and passing the new absolute path to
*sdsu.main()* as the *securityRoot* parameter. For example, you are *strongly*
encouraged to use your own certificates.

staticRoot
----------

The */static* subdirectory contains static files that will be served to satisfy
HTTP requests. Except for *splash.html*, all static files are protected by
authentication restrictions. Default contents of */static* include:

* *index.css*, a stylesheet used by *index.html* and placed here to demonstrate
  and verify protection of static file contents.

* *index.html*, the default landing page for authenticated users.

* *splash.html*, which defines the login page for users that have not yet been
  authenticated. This also serves as a logout page, as upon accessing this
  resource any existing sessions are cleared.

Users can customize static file contents (and therefore the bulk of their web
applications) by creating a new copy of this directory, modifying it's
contents, and passing the new absolute path to *sdsu.main()* as the
*staticRoot* parameter.

wssHandlerCls
-------------

The class *sdsu.WssHandler* defines the default behavior for secure WebSocket
interaction mounted by the server to the path "/wss". Users can customize
WebSocket behaviors by inheriting from this class, then pass the new child
class to *sdsu.main()* as the *wssHandlerCls* parameter. The following methods
should be implemented:

* *open()*

* *on_message()* (by default, simply echoes the message back to the client)

* *on_close()*

See class method documentation for more details, including method signatures.
Keep in mind that each instance of the WebSocker handler class is unique to
a specific client connection; state is not shared between clients.
