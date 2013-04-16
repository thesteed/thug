# Sina DLoader Class ActiveX Control 'DonwloadAndInstall' 
# Method Arbitrary File Download Vulnerability

import logging
log = logging.getLogger("Thug")

def DownloadAndInstall(self, url):
    log.ThugLogging.add_behavior_warn("[SinaDLoader Downloader ActiveX] Fetching from URL %s" % (url, ))
    log.ThugLogging.log_exploit_event(self._window.url,
                                      "SinaDLoader Downloader ActiveX",
                                      "Fetching from URL",
                                      data = {
                                                "url": url
                                             },
                                      forward = False)

    try:
        response, content = self._window._navigator.fetch(url, redirect_type = "SinaDLoader Exploit")
    except:
        log.ThugLogging.add_behavior_warn('[SinaDLoader Downloader ActiveX] Fetch failed')
        return

    if response.status == 404:
        log.ThugLogging.add_behavior_warn("[SinaDLoader Downloader ActiveX] FileNotFoundError: %s" % (url, ))
