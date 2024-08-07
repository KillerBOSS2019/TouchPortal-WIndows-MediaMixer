import win32gui
import win32con
import ctypes
import threading
import os
from pycaw.pycaw import AudioUtilities
from logging import getLogger

from audioUtil.utils import getActiveExecutablePath
from tppEntry import TP_PLUGIN_STATES, TP_PLUGIN_INFO, TP_PLUGIN_CONNECTORS, __version__
import TouchPortalAPI as TP

g_log = getLogger(__name__)

class WindowFocusListener:
    def __init__(self, TPClient:TP.Client):
        self.hook = None
        self.win_event_proc = None
        self.running = False
        self.thread = None
        
        self.TPClient = TPClient
        self.current_app_connector_id = f"pc_{TP_PLUGIN_INFO['id']}_{TP_PLUGIN_CONNECTORS['APP Volume Slider']['id']}|{TP_PLUGIN_CONNECTORS['APP Volume Slider']['data']['appchoice']['id']}=Current app"
        
        self.current_focused_name = ""
        self.current_focused_exe_path = ""
        self.last_volume = None
        self.last_mute = None


    def callback(self, hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime):
        if event == win32con.EVENT_SYSTEM_FOREGROUND:
            window_title = win32gui.GetWindowText(hwnd)
            executable_path = getActiveExecutablePath()
            if executable_path:
                self.current_focused_exe_path = executable_path
                process_name = os.path.basename(executable_path)
                
                self.update_process_states(process_name)

                g_log.info(f"Window focus changed to: {window_title} | Process: {process_name}")

    def win_event_loop(self):
        WinEventProcType = ctypes.WINFUNCTYPE(
            None, 
            ctypes.wintypes.HANDLE,
            ctypes.wintypes.DWORD,
            ctypes.wintypes.HWND,
            ctypes.wintypes.LONG,
            ctypes.wintypes.LONG,
            ctypes.wintypes.DWORD,
            ctypes.wintypes.DWORD
        )
        
        self.win_event_proc = WinEventProcType(self.callback)
        
        user32 = ctypes.windll.user32
        self.hook = user32.SetWinEventHook(
            win32con.EVENT_SYSTEM_FOREGROUND,
            win32con.EVENT_SYSTEM_FOREGROUND,
            0,
            self.win_event_proc,
            0,
            0,
            win32con.WINEVENT_OUTOFCONTEXT
        )

        if self.hook == 0:
            g_log.info("Failed to set up event hook")
            return

        msg = ctypes.wintypes.MSG()
        while self.running:
            if user32.GetMessageA(ctypes.byref(msg), 0, 0, 0) != 0:
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageA(ctypes.byref(msg))

    def start(self):
        if self.running:
            g_log.info("windowFocusListener is already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self.win_event_loop)
        self.thread.start()
        g_log.info("windowFocusListener started")

    def stop(self):
        if self.hook:
            self.running = False
            ctypes.windll.user32.PostThreadMessageA(self.thread.ident, win32con.WM_QUIT, 0, 0)
            self.thread.join()
            ctypes.windll.user32.UnhookWinEvent(self.hook)
            self.hook = None
            self.win_event_proc = None
            
            g_log.info("Stopped listening for focus changes.")

    def get_app_path(self):
        return self.current_focused_exe_path
    
    def get_volume(self, session):
        if session:
            interface = session.SimpleAudioVolume
            return interface.GetMasterVolume()
        return None
    
    def get_mute(self, session):
        if session:
            interface = session.SimpleAudioVolume
            return interface.GetMute()
        return None

    def get_session(self, process_name):
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            if session.Process and session.Process.name() == process_name:
                return session
        return None

    def update_process_states(self, process_name):
        session = self.get_session(process_name)
        
        if process_name != self.current_focused_name:
            self.TPClient.stateUpdate(TP_PLUGIN_STATES['FocusedAPP']['id'], process_name)
            self.current_focused_name = process_name

        if not session:
            
            return

        current_app_volume = self.get_volume(session)
        current_app_mute = self.get_mute(session)

        volume_int = int(current_app_volume * 100) if current_app_volume is not None else 0

        # Update volume if it has changed
        if volume_int != self.last_volume:
            if current_app_connector_shortid := self.TPClient.shortIdTracker.get(self.current_app_connector_id, None):
                self.TPClient.shortIdUpdate(current_app_connector_shortid, volume_int)
            self.TPClient.stateUpdate(TP_PLUGIN_STATES['currentAppVolume']['id'], str(volume_int))
            self.last_volume = volume_int

        # Update mute state if it has changed
        if current_app_mute != self.last_mute:
            mute_state = "Muted" if current_app_mute else "Un-muted"
            self.TPClient.stateUpdate(TP_PLUGIN_STATES['currentAppMute']['id'], mute_state)
            self.last_mute = current_app_mute

if __name__ == "__main__":
    listener = WindowFocusListener()
    try:
        listener.start()
        input("Press Enter to stop...")
    finally:
        listener.stop()