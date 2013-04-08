#!/usr/bin/env python
#
# Location.py
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA  02111-1307  USA

import PyV8
import logging

try:
    from . import Window
    from . import DFT
except ImportError:
    import Window
    import DFT

from .W3C import *

try:
    import urllib.parse as urlparse
except ImportError:
    import urlparse

log = logging.getLogger("Thug")

class Location(PyV8.JSClass):
    def __init__(self, window):
        self._window = window

    def toString(self):
        return self._window.url

    @property
    def parts(self):
        return urlparse.urlparse(self._window.url)

    def get_href(self):
        return self._window.url

    def set_href(self, url):
        referer = self._window.url
        if referer == url:
            log.warning("Detected redirection from %s to %s... skipping" % (referer, url, ))
            return

        for p in log.ThugOpts.Personality:
            if log.ThugOpts.Personality[p]['userAgent'] == self._window._navigator.userAgent:
                break

        log.ThugLogging.log_href_redirect(referer, url)

        doc    = w3c.parseString('')
        window = Window.Window(referer, doc, personality = p)
        window = window.open(url)
        if not window:
            return

        #self._window.url = url
        dft = DFT.DFT(window)
        dft.run()

    href = property(get_href, set_href)

    @property
    def protocol(self):
        return self.parts.scheme

    @property
    def host(self):
        return self.parts.netloc

    @property
    def hostname(self):
        return self.parts.hostname

    @property
    def port(self):
        return self.parts.port

    @property
    def pathname(self):
        return self.parts.path

    @property
    def search(self):
        return self.parts.query

    @property
    def hash(self):
        return self.parts.fragment

    def assign(self, url):
        """Loads a new HTML document."""
        self._window.open(url)

    def reload(self, force = False):
        """Reloads the current page."""
        self._window.open(self._window.url)

    def replace(self, url):
        """Replaces the current document by loading another document at the specified URL."""
        self.href = url
