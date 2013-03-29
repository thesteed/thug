#!/usr/bin/env python
#
# thug.py
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

import sys
import os
import getopt
import logging
from thug import Thug

from ThugAPI import *
from Plugins.ThugPlugins import *

log = logging.getLogger("Thug")
log.setLevel(logging.WARN)


class Thugs(Thug):
    def __init__(self, args=None):
        Thug.__init__(self, args)
        
    def analyze_url(self, url):
        self.log_init(url)
        ThugPlugins(PRE_ANALYSIS_PLUGINS, self)()
        self.run_remote(url)
        ThugPlugins(POST_ANALYSIS_PLUGINS, self)()

        self.log_event()
        return log


if __name__ == "__main__":
    if not os.getenv('THUG_PROFILE', None):
        Thugs(sys.argv[1:])()
    else:
        import cProfile
        import pstats
        cProfile.run('Thugs(sys.argv[1:])()', 'countprof')
        p = pstats.Stats('countprof')
        p.print_stats()
