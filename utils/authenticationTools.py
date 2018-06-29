import urllib2
import urllib
import httplib
import cookielib
from client_properties import *



class HTTPSClientAuthHandler(urllib2.HTTPSHandler):
    ''' Handles our HTTPS Cert authentication (in the case of a self-signed cert) '''
    def __init__(self, cert):
        urllib2.HTTPSHandler.__init__(self)
        self.cert = cert
        if enable_https:
            self.ssl_context = ssl.create_default_context(cafile=self.cert)
        else:
            self.ssl_context = None

    def https_open(self, req):
        # Rather than pass in a reference to a connection class, we pass in
        # a reference to a function which, for all intents and purposes,
        # will behave as a constructor
        return self.do_open(self.getConnection, req)

    def getConnection(self, host, timeout=300):
        if enable_https:
            return httplib.HTTPSConnection(host=host, context=self.ssl_context)
        return httplib.HTTPConnection(host=host)  # ^ spot the differences


class SendDataService:

    def __init__(self, username, password):
        self.username = username      # this user will need to be setup via
        self.password = password  # the admin console

        self.cookie_jar = cookielib.CookieJar()  # where we store our CSRF token

        self.opener = urllib2.build_opener(
            urllib2.HTTPHandler(debuglevel=DEBUG_LEVEL),
            HTTPSClientAuthHandler(cert_file),
            urllib2.HTTPCookieProcessor(self.cookie_jar)
        )  # ^ where we work our CSRF/SSL magic - DO NOT TOUCH UNLESS VERY SURE

        self.http_headers = [("X-requested-with", "XMLHttpRequest")]
        self.opener.addheaders = self.http_headers

    def _send_request(self, given_url, data=None):
        if data is None:
            # If we're not sending data then we're trying to get a CSRF token
            # hence we send no data
            request = urllib2.Request(given_url)
        else:
            headers = {"Content-Type": "application/x-www-form-urlencoded", "Referer": given_url}
            request = urllib2.Request(
                given_url, urllib.urlencode(data), headers
            )
        page = self.opener.open(request).read()
        if 'FAILURE' in page:
            print page
            raise Exception('SERVER RESPONDED WITH FAILURE')

    def _set_csrf_token(self):
        """Copies the cookie to the header of the subsequent request"""
        csrf_cookies = {cookie for cookie in self.cookie_jar if cookie.name == "csrftoken"}
        if csrf_cookies:
            assert len(csrf_cookies) == 1
            self.opener.addheaders = self.http_headers + [("X-CSRFToken", csrf_cookies.pop().value)]

    def send_data(self, given_url, data):
        # Send GET to have a CSRF token returned
        # then send the POST with the data

        # "username": self.username,
        # "password": self.password,
        data["username"] = self.username
        data["password"] = self.password

        self._send_request(given_url)
        self._set_csrf_token()
        self._send_request(given_url, data)
        self._set_csrf_token()
        return True

