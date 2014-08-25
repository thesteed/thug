#!/usr/bin/env python
#
# ThugLogging.py
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

from .BaseLogging import BaseLogging
from .SampleLogging import SampleLogging
from virustotal.VirusTotal import VirusTotal
from honeyagent.HoneyAgent import HoneyAgent

try:
    import configparser as ConfigParser
except ImportError:
    import ConfigParser

import os
import copy
import datetime

import logging
log = logging.getLogger("Thug")

class ThugLogging(BaseLogging, SampleLogging):
    eval_min_length_logging = 4

    def __init__(self, thug_version):
        BaseLogging.__init__(self)
        SampleLogging.__init__(self)

        self.thug_version   = thug_version
        self.VirusTotal     = VirusTotal()
        self.HoneyAgent     = HoneyAgent()
        self.baseDir        = None
        self.windows        = dict()
        self.shellcodes     = set()
        self.shellcode_urls = set()
        self.methods_cache  = dict()

        self.__init_config()

    def __init_config(self):
        self.modules = dict()
        config       = ConfigParser.ConfigParser()

        conf_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logging.conf')
        config.read(conf_file)

        modules = config.items('modules')
        for name, module in modules:
            if self.check_module(name, config):
                self.modules[name.strip()] = self.__init_module(module)

    def __init_module(self, source):
        module = __import__(source)
        components = source.split('.')
        for component in components[1:]:
            module = getattr(module, component)

        p = None
        handler = getattr(module, component, None)
        if handler:
            p = handler(self.thug_version)

        return p

    def resolve_method(self, name):
        if name in self.methods_cache.keys():
            return self.methods_cache[name]

        methods = []

        for module in self.modules.values():
            m = getattr(module, name, None)
            if m:
                methods.append(m)

        self.methods_cache[name] = methods
        return methods

    def set_url(self, url):
        for m in self.resolve_method('set_url'):
            m(url)

    def add_behavior_warn(self, description = None, cve = None, method = "Dynamic Analysis"):
        for m in self.resolve_method('add_behavior_warn'):
            m(description, cve, method)

    def check_snippet(self, s):
        return len(s) < self.eval_min_length_logging

    def add_code_snippet(self, snippet, language, relationship, method = "Dynamic Analysis", check = False):
        if check and self.check_snippet(snippet):
            return

        for m in self.resolve_method('add_code_snippet'):
            m(snippet, language, relationship, method)

    def log_file(self, data, url = None, params = None):
        sample = self.build_sample(data, url)
        if sample is None:
            return None
        
        for m in self.resolve_method('log_file'):
            m(copy.deepcopy(sample))

        self.VirusTotal.analyze(data, sample['md5'], self.baseDir)

        if sample['type'] in ('JAR', ):
            self.HoneyAgent.analyze(data, sample['md5'], self.baseDir, params)

        log.SampleClassifier.classify(data, sample['md5'])
        return sample

    def log_event(self):
        log.warning("Saving log analysis at %s" % (self.baseDir, ))

        for m in self.resolve_method('export'):
            m(self.baseDir)

        for m in self.resolve_method('log_event'):
            m(self.baseDir)

    def log_connection(self, source, destination, method, flags = {}):
        """
        Log the connection (redirection, link) between two pages

        @source         The origin page
        @destination    The page the user is made to load next
        @method         Link, iframe, .... that moves the user from source to destination
        @flags          Additional information flags. Existing are: "exploit"
        """
        for m in self.resolve_method('log_connection'):
            m(source, destination, method, flags)

    def log_location(self, url, ctype, md5, sha256, flags = {}, fsize = 0, mtype = ""):
        """
        Log file information for a given url

        @url            Url we fetched this file from
        @ctype          Content type (whatever the server says it is)
        @md5            MD5 hash
        @sha256         SHA256 hash
        @fsize          File size
        @mtype          Calculated mime type
        """

        for m in self.resolve_method('log_location'):
            m(url, ctype, md5, sha256, flags = flags, fsize = fsize, mtype = mtype)

    def log_exploit_event(self, url, module, description, cve = None, data = None, forward = True):
        """
        Log file information for a given url

        @url            Url where this exploit occured
        @module         Module/ActiveX Control, ... that gets exploited
        @description    Description of the exploit
        @cve            CVE number (if available)
        @forward        Forward log to add_behavior_warn
        """
        if forward:
            self.add_behavior_warn("[%s] %s" % (module, description, ), cve = cve)

        for m in self.resolve_method('log_exploit_event'):
            m(url, module, description, cve = cve, data = data)

    def log_warning(self, data):
        log.warning(data)

        for m in self.resolve_method('log_warning'):
            m(data)

    def log_redirect(self, response):
        if not response:
            return None

        if response.previous is None:
            return None

        redirects = list()
        r         = response
        final     = response['content-location'] if 'content-location' in response else None

        while r.previous:
            if final is None and 'location' in r.previous:
                final = r.previous['location']

            redirects.append(r.previous)
            r = r.previous

        while len(redirects):
            p = redirects.pop()
            log.URLClassifier.classify(p['content-location'])
            self.add_behavior_warn("[HTTP Redirection (Status: %s)] Content-Location: %s --> Location: %s" % (p['status'],
                                                                                                              p['content-location'],
                                                                                                              p['location'], ))
            self.log_connection(p['content-location'], p['location'], "http-redirect")
            last = p['location']

        return final

    def log_href_redirect(self, referer, url):
        self.add_behavior_warn("[HREF Redirection (document.location)] Content-Location: %s --> Location: %s" % (referer, url, ))
        self.log_connection(referer, url, "href")
