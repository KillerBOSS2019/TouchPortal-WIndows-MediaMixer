from ctypes import windll
import psutil
import win32process
import comtypes
from comtypes import COMError
from pycaw.pycaw import EDataFlow, ERole

from audioUtil import audioSwitch
from tppEntry import __version__


dataMapper = {
            "Output": EDataFlow.eRender.value,
            "Input": EDataFlow.eCapture.value,
            "Default": ERole.eMultimedia.value,
            "Communications": ERole.eCommunications.value
        }


def getActiveExecutablePath():
    hWnd = windll.user32.GetForegroundWindow()
    if hWnd == 0:
        return None # Note that this function doesn't use GetLastError().
    else:
        _, pid = win32process.GetWindowThreadProcessId(hWnd)
        return psutil.Process(pid).exe()



STGM_READ = 0x00000000
def getDevicebydata(edata, erole):
    DEVPKEY_Device_FriendlyName = "{a45c254e-df1c-4efd-8020-67d146a850e0} 14".upper()

    device = ""
    audioDevice = None

    comtypes.CoInitialize()
    try:
        audioDevice = audioSwitch.MyAudioUtilities.GetDeviceState(edata, erole)
        if audioDevice:
            properties = {}
            store = audioDevice.OpenPropertyStore(STGM_READ)
            try:
                propCount = store.GetCount()
                for j in range(propCount):
                    pk = store.GetAt(j)
                    value = store.GetValue(pk)
                    v = value.GetValue()
                    value.clear()

                    name = str(pk)
                    properties[name] = v
                device = properties.get(DEVPKEY_Device_FriendlyName, "")

            finally:
                value.clear()
                store.Release()
                del store
                del properties

    except COMError as exc:
        pass

    finally:
        if audioDevice:
            audioDevice.Release()
            del audioDevice
        comtypes.CoUninitialize()
    return str(device)
        