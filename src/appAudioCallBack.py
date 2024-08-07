#### Cant figure out how to pass args to the magic session client hingy...... it doesnt allow me..

import os
from logging import getLogger
from time import sleep

from comtypes import COMError
from pycaw.magic import MagicSession
from pycaw.constants import AudioSessionState

from windowFocusListener import WindowFocusListener
import TouchPortalAPI as TP
from tppEntry import PLUGIN_ID, TP_PLUGIN_ACTIONS, TP_PLUGIN_CONNECTORS, TP_PLUGIN_INFO, TP_PLUGIN_STATES, __version__

g_log = getLogger(__name__)

class VolumeProcess:
    def __init__(self, tpClient:TP.Client):
        self.volume_process = ["Master Volume", "Current app"]
        self.audio_ignore_list = []
        self.TPClient = tpClient
        
    @classmethod
    def set_tp_client(cls, client):
        cls.tp_client = client
        
    def updateVolumeMixerChoicelist(self):
        self.TPClient.choiceUpdate(TP_PLUGIN_ACTIONS["Inc/DecrVol"]['data']['AppChoice']['id'], self.volume_process[1:])
        self.TPClient.choiceUpdate(TP_PLUGIN_ACTIONS["AppMute"]['data']['appChoice']['id'], self.volume_process[1:])
        self.TPClient.choiceUpdate(TP_PLUGIN_CONNECTORS["APP Volume Slider"]["data"]["appchoice"]['id'], self.volume_process)
        self.TPClient.choiceUpdate(TP_PLUGIN_ACTIONS["AppAudioSwitch"]["data"]["AppChoice"]["id"], self.volume_process[1:])
    
    def removeAudioState(self, app_name):
        if self.TPClient.currentStates.get(PLUGIN_ID + f".createState.{app_name}.muteState"):
            self.TPClient.removeStateMany([
                        PLUGIN_ID + f".createState.{app_name}.muteState",
                        PLUGIN_ID + f".createState.{app_name}.volume",
                        PLUGIN_ID + f".createState.{app_name}.active"
                        ])
            self.volume_process.remove(app_name)
            self.updateVolumeMixerChoicelist() # Update with new changes
        else:
            g_log.info("AudioState not present")
    
    def audioStateManager(self, app_name):
        g_log.debug(f"AUDIO EXEMPT LIST {self.audio_ignore_list}")
    
        if app_name not in self.volume_process:
            g_log.info("Creating states")
            self.TPClient.createStateMany([
                    {   
                        "id": PLUGIN_ID + f".createState.{app_name}.muteState",
                        "desc": f"{app_name} Mute State",
                        "parentGroup": "Audio process state",
                        "value": ""
                    },
                    {
                        "id": PLUGIN_ID + f".createState.{app_name}.volume",
                        "desc": f"{app_name} Volume",
                        "parentGroup": "Audio process state",
                        "value": ""
                    },
                    {
                        "id": PLUGIN_ID + f".createState.{app_name}.active",
                        "desc": f"is {app_name} Active",
                        "parentGroup": "Audio process state",
                        "value": ""
                    },
                    ])
            self.volume_process.append(app_name)
    
            """UPDATING CHOICES"""
            self.updateVolumeMixerChoicelist()
            g_log.debug(f"{app_name} state added")
    
        """ Checking for Exempt Audio"""
        if app_name in self.audio_ignore_list:
            self.removeAudioState(app_name)
            return True
        return False
        

class AppAudioCallBack(MagicSession):
    @classmethod
    def set_tp_client(cls, client, volume_process, listener):
        cls.TPClient:TP.Client = client
        cls.volume_process:VolumeProcess = volume_process
        cls.listener:WindowFocusListener = listener

        
    def __init__(self):
        super().__init__(
            volume_callback=self.update_volume,
            mute_callback=self.update_mute,
            state_callback=self.update_state
        )
        self.app_name = self.magic_root_session.app_exec

        if self.app_name not in self.volume_process.audio_ignore_list:
            # set initial:
            self.update_mute(self.mute)
            self.update_state(self.state)
            self.update_volume(self.volume)
        

            
    def update_state(self, new_state):
        """
        when status changed
        (see callback -> AudioSessionEvents -> OnStateChanged)
        """
        
        if self.app_name not in self.volume_process.audio_ignore_list:
            if new_state == AudioSessionState.Inactive:
                # AudioSessionStateInactive
                """Sesssion is Inactive"""
                g_log.debug(f"{self.app_name} not active")
                self.TPClient.stateUpdate(PLUGIN_ID + f".createState.{self.app_name}.active","False")
    
            elif new_state == AudioSessionState.Active:
                """Session Active"""
                g_log.debug(f"{self.app_name} is an Active Session")
                self.TPClient.stateUpdate(PLUGIN_ID + f".createState.{self.app_name}.active","True")
    
        if new_state == AudioSessionState.Expired:
            """Removing Expired States"""
            self.volume_process.removeAudioState(self.app_name)

    
    def update_volume(self, new_volume):
        """
        when volume is changed externally - Updating Sliders and Volume States
        (see callback -> AudioSessionEvents -> OnSimpleVolumeChanged )
        """
        if self.app_name not in self.volume_process.audio_ignore_list:
            self.TPClient.stateUpdate(PLUGIN_ID + f".createState.{self.app_name}.volume", str(round(new_volume*100)))
            app_connector_id =f"pc_{TP_PLUGIN_INFO['id']}_{TP_PLUGIN_CONNECTORS['APP Volume Slider']['id']}|{TP_PLUGIN_CONNECTORS['APP Volume Slider']['data']['appchoice']['id']}={self.app_name}"
            
            if app_connector_shortId := self.TPClient.shortIdTracker.get(app_connector_id, None):
                self.TPClient.shortIdUpdate(app_connector_shortId, round(new_volume * 100))

            """Checking for Current App If Its Active, Adjust it also"""
            if (activeWindow := self.listener.get_app_path()) != "":
                current_app_connector_id = f"pc_{TP_PLUGIN_INFO['id']}_{TP_PLUGIN_CONNECTORS['APP Volume Slider']['id']}|{TP_PLUGIN_CONNECTORS['APP Volume Slider']['data']['appchoice']['id']}=Current app"
                if self.listener.current_focused_name == self.app_name:
                    if current_app_connector_shortId := self.TPClient.shortIdTracker.get(current_app_connector_id, None):
                        if self.listener.last_volume != new_volume:
                            self.TPClient.shortIdUpdate(
                                current_app_connector_shortId,
                                int(new_volume * 100) if os.path.basename(activeWindow) == self.app_name else 0)
                            
                            self.listener.last_volume != new_volume
                        
                    self.TPClient.stateUpdate(TP_PLUGIN_STATES['currentAppVolume']['id'], str(int(new_volume * 100)))
                    
            g_log.debug(f"Volume: {self.app_name} - {new_volume}")
       
            
    def update_mute(self, muted):
        """ when mute state is changed by user or through other app """
        if self.app_name not in self.volume_process.audio_ignore_list:
            isDeleted = self.volume_process.audioStateManager(self.app_name)
            if not isDeleted:
                self.TPClient.stateUpdate(PLUGIN_ID + f".createState.{self.app_name}.muteState", "Muted" if muted else "Un-muted")
                
                if self.listener.current_focused_name == self.app_name:
                    self.TPClient.stateUpdate(TP_PLUGIN_STATES['currentAppMute']['id'], "Muted" if muted else "Un-muted")

                g_log.debug(f"Mute State: {self.app_name} - {'Muted' if muted else 'Un-muted'}")


