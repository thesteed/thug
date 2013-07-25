#!/usr/bin/env python
#
# Mapper.py
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
#
# Author:   Thorsten Sick <thorsten.sick@avira.com> from Avira
#           (developed for the iTES Project http://ites-project.org)
#
# Changes:
#           - pydot support
#             Angelo Dell'Aera <angelo.dellaera@honeynet.org>

import os
import json
import fnmatch
import pydot

try:
    import urllib.parse as urlparse
except ImportError:
    import urlparse


class DictDiffer(object):
    """
    Calculate the difference between two dictionaries as:
    (1) items added
    (2) items removed
    (3) keys same in both but changed values
    (4) keys same in both and unchanged values
    """
    def __init__(self, current_dict, past_dict):
        self.current_dict = current_dict
        self.past_dict    = past_dict
        self.set_current  = set(current_dict.keys())
        self.set_past     = set(past_dict.keys())
        self.intersect    = self.set_current.intersection(self.set_past)

    def added(self):
        return self.set_current - self.intersect

    def removed(self):
        return self.set_past - self.intersect

    def changed(self):
        return set(o for o in self.intersect if self.past_dict[o] != self.current_dict[o])

    def unchanged(self):
        return set(o for o in self.intersect if self.past_dict[o] == self.current_dict[o])

    def anychange(self):
        if len(self.added()):
            return True

        if len(self.removed()):
            return True

        if len(self.changed()):
            return True

        return False


class Mapper():
    """
        Map URL relationships
    """

    markup_types = ("text/html",
                    "text/xml",
                    "text/css", )

    image_types  = ("image/", )

    exec_types   = ("application/javascript",
                    "text/javascript",
                    "application/x-javascript")

    def __init__(self, resdir, simplify = False):
        """
        @resdir     : Directory to store the result svg in
        @simplify   : Reduce the urls to server names
        """
        self.resdir   = resdir
        self.simplify = simplify
        self.svgfile  = os.path.join(self.resdir, "graph.svg")

        self.data = {
                        "locations"   : [],
                        "connections" : []
                    }

        self.first_track = True   # flag indicating that we did not follow a track yet
        self._init_graph()

    def _init_graph(self):
        """
            Write the dot header
        """
        self.graph = pydot.Dot(graph_type = 'digraph', rankdir = 'LR')

    def _check_content_type(self, loc, t):
        return loc["content-type"] and loc["content-type"].lower().startswith(t)

    def _check_types(self, loc, _types):
        for t in _types:
            if self._check_content_type(loc, t):
                return True

        return False

    def check_markup(self, loc):
        return self._check_types(loc, self.markup_types)

    def check_image(self, loc):
        return self._check_types(loc, self.image_types)

    def check_exec(self, loc):
        return self._check_types(loc, self.exec_types)

    def get_shape(self, loc):
        # Markup
        if self.check_markup(loc):
            return "box"

        # Images
        if self.check_image(loc):
            return "oval"

        # Executable stuff
        if self.check_exec(loc):
            return "hexagon"

        return None

    def get_fillcolor(self, loc):
        if "error" in loc["flags"]:
            return "orange"

        return None

    def get_color(self, con):
        if "method" in ["iframe"]:
            return "orange"

        return None

    def _normalize(self, p):
        if not p.startswith('"'):
            return '"%s"' % (p, )

        return p

    def _dot_from_data(self):
        # Create dot from data
        if "locations" in self.data:
            for loc in self.data["locations"]:
                if loc["display"] is False:
                    continue

                url = self._normalize(loc["url"])

                node = pydot.Node(url)
                node.set_label(url)

                shape = self.get_shape(loc)
                if shape:
                    node.set_shape(shape)

                fillcolor = self.get_fillcolor(loc)
                if fillcolor:
                    node.set_style('filled')
                    node.set_fillcolor(fillcolor)

                node.set_fontname('arial')
                node.set_fontsize(7)
                self.graph.add_node(node)

        if "connections" in self.data:
            # Add edges
            for con in self.data["connections"]:
                if con["display"] is False:
                    continue

                color = self.get_color(con)

                source      = self._normalize(con["source"])
                destination = self._normalize(con["destination"])

                edge = pydot.Edge(source, destination)
                edge.set_label(con['method'])

                if color:
                    edge.set_color(color)

                edge.set_fontname('arial')
                edge.set_fontsize(7)
                self.graph.add_edge(edge)

    def _add_to_loc(self, loc):
        """
            Add location information to location data
        """
        loc["display"] = True

        if self.simplify:
            url = urlparse.urlparse(loc["url"]).netloc
            if url:
                loc["url"] = url

        for a in self.data["locations"]:
            d = DictDiffer(a, loc)
            if not d.anychange():
                return

        self.data["locations"].append(loc)

    def _add_weak_loc(self, url):
        """
        Generate a weak loc for the given url.
        """

        for al in self.data["locations"]:
            if al["url"] == url:
                return

        loc = {'mimetype'       : '',
               'url'            : url,
               'size'           : 0,
               'flags'          : {},
               'sha256'         : None,
               'content-type'   : None,
               'display'        : True,
               'md5'            : None}

        self._add_to_loc(loc)

    def _add_to_con(self, con):
        """
            Add connection information to connection data
        """
        con["display"] = True

        if self.simplify:
            url = urlparse.urlparse(con["source"]).netloc
            if url:
                con["source"] = url

            url = urlparse.urlparse(con["destination"]).netloc
            if url:
                con["destination"] = url

        self._add_weak_loc(con["source"])
        self._add_weak_loc(con["destination"])

        for a in self.data["connections"]:
            d = DictDiffer(a, con)
            if not d.anychange():
                return

        self.data["connections"].append(con)

    def add_data(self, data):
        # Add nodes
        if "locations" in data:
            for loc in data["locations"]:
                self._add_to_loc(loc)

        if "connections" in data:
            for con in data["connections"]:
                self._add_to_con(con)

    def add_file(self, filename):
        """
            Add data file
        """
        try:
            self.add_data(json.load(open(filename, "r")))
        except ValueError:
            pass

    def write_svg(self):
        """
            Create SVG file
        """
        self._dot_from_data()

        try:
            self.graph.write_svg(self.svgfile)
        except:
            pass

    def _activate(self, conto):
        """
            Iterate through data and set display for hot connections
        """

        tofix = []

        for c in self.data["connections"]:
            if c["display"] is False and c["destination"] == conto:
                c["display"] = True
                tofix.append(c["source"])

        for l in self.data["locations"]:
            if l["url"] == conto or l["url"] in tofix:
                l["display"] = True

        for t in tofix:
            self._activate(t)

    def follow_track(self, end):
        """
            Follow the track between entry point of the analysis and the exploit URL.
            Remove all non-relevant stuff

            @end: end url to track the connections to
        """

        if self.first_track:
            for con in self.data["connections"]:
                con["display"] = False

            for loc in self.data["locations"]:
                loc["display"] = False

        self.first_track = False
        self._activate(end)

    def write_text(self):
        """ Return text representation
        """

        res = ""
        for con in self.data["connections"]:
            if con["display"]:
                res += "%s -- %s --> %s \n" % (str(con["source"]),str(con["method"]), str(con["destination"]))
        return res


def allFiles(root, patterns = "*", single_level = False, yield_folders = False):
    """
        Walk files
    """

    patterns = patterns.split(";")
    for path, subdirs, files in os.walk(root):
        if yield_folders:
            files.extend(subdirs)

        files.sort()

        for name in files:
            for pattern in patterns:
                if fnmatch.fnmatch(name, pattern):
                    yield os.path.join(path, name)
                    break

        if single_level:
            break

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description = 'Receives jobs and starts Thug to process them')
    parser.add_argument('--resdir', help = 'Result dir', default = ".")
    parser.add_argument('--source', help = 'Source file or dir', default = "avlog.json")
    parser.add_argument('--simplify', help = 'Reduce the URLs to servernames', default = False, action = "store_true")
    parser.add_argument('--tracks', type=str, nargs='+', help='URLs to track to', default = None)

    args = parser.parse_args()

    m = Mapper(args.resdir, simplify = args.simplify)
    if os.path.isdir(args.source):
        for afile in allFiles(args.source, "avlog.json"):
            #print afile
            m.add_file(afile)
    else:
        m.add_file(args.source)

    if args.tracks:
        for atrack in args.tracks:
            m.follow_track(atrack)
    #print m.write_text()
    m.write_svg()
