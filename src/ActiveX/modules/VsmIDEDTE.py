
import logging
log = logging.getLogger("Thug")

def CreateObject(self, object, param = ''):
    import ActiveX

    log.ThugLogging.add_behavior_warn("[VsmIDE.DTE ActiveX] CreateObject (%s)" % (object))
    log.ThugLogging.log_exploit_event(self._window.url,
                                      "VsmIDE.DTE ActiveX",
                                      "CreateObject",
                                      data = {
                                                "object": object
                                             },
                                      forward = False)

    return ActiveX.ActiveX._ActiveXObject(self._window, object)

