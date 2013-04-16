# Symantec AppStream LaunchObj ActiveX Arbitrary File Download and Execute
# CVE-2008-4388

import logging
log = logging.getLogger("Thug")

def installAppMgr(self, url):
    log.ThugLogging.log_exploit_event(self._window.url,
                                      "Symantec AppStream LaunchObj ActiveX",
                                      "Arbitrary File Download and Execute",
                                      cve = "CVE-2088-4388",
                                      data = {
                                                "url": url
                                             }
                                     )

    log.ThugLogging.add_behavior_warn("[Symantec AppStream LaunchObj ActiveX] Fetching from URL %s" % (url, ))

    try:
        response, content = self._window._navigator.fetch(url, redirect_type = "CVE-2088-4388")
    except:
        log.ThugLogging.add_behavior_warn('[Symantec AppStream LaunchObj ActiveX] Fetch failed')
