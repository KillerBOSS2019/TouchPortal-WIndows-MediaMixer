import time
import comtypes
from pycaw.constants import CLSID_MMDeviceEnumerator
from pycaw.pycaw import (DEVICE_STATE, AudioUtilities, EDataFlow,
                         IMMDeviceEnumerator)

import threading
import pythoncom
from pycaw.constants import EDataFlow, DEVICE_STATE, ERole
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from pycaw.callbacks import MMNotificationClient
from ctypes import POINTER, cast
from comtypes import CLSCTX_ALL, COMObject
from pycaw.api.endpointvolume import IAudioEndpointVolumeCallback
from pycaw.api.endpointvolume.depend import AUDIO_VOLUME_NOTIFICATION_DATA
from logging import getLogger

from tppEntry import TP_PLUGIN_INFO, TP_PLUGIN_CONNECTORS, TP_PLUGIN_STATES, PLUGIN_ID, __version__
from audioUtil import audioSwitch
import TouchPortalAPI as TP


g_log = getLogger(__name__)

class AudioEndpointVolumeCallback(COMObject):
    """
    A class that implements the IAudioEndpointVolumeCallback interface for handling
    audio endpoint volume notifications.

    This class is used to receive volume change notifications and mute state changes 
    for audio endpoints. It is initialized with the type, name, and ID of the device 
    it is monitoring.

    Attributes:
        device_type (str): The type of the audio device (e.g., 'input' or 'output').
        device_name (str): The friendly name of the audio device.
        device_id (str): The unique ID of the audio device.

    Methods:
        OnNotify(pNotify):
            Called when the volume or mute state of the audio device changes. 
            Prints the device type, mute status, volume level, and device name.
    """
    
    _com_interfaces_ = [IAudioEndpointVolumeCallback]

    def __init__(self, device_type, device_name, device_id, audio_manager, tpClient):
        """
        Initializes the AudioEndpointVolumeCallback instance.

        Args:
            device_type (str): The type of the audio device (e.g., 'input' or 'output').
            device_name (str): The friendly name of the audio device.
            device_id (str): The unique ID of the audio device.
        """
        super().__init__()
        self.device_type = device_type
        self.device_name = device_name
        self.device_id = device_id
        self.audio_manager:AudioManager = audio_manager
        self.TPClient:TP.Client = tpClient

    def OnNotify(self, pNotify):
        """
        Handles volume and mute state change notifications.

        This method is called by the system when there are changes to the volume
        or mute state of the associated audio device. It prints the device type,
        current mute state, volume level, and the device name.

        Args:
            pNotify (POINTER(AUDIO_VOLUME_NOTIFICATION_DATA)): A pointer to an 
                AUDIO_VOLUME_NOTIFICATION_DATA structure that contains information 
                about the volume and mute state of the device.
        """
        notify_data = cast(pNotify, POINTER(AUDIO_VOLUME_NOTIFICATION_DATA)).contents
        master_volume = round(notify_data.fMasterVolume * 100)
        #         # g_log.info(f"Event Context: {notify_data.guidEventContext}")
        #         # g_log.info(f"Muted: {notify_data.bMuted}")
        #         # g_log.info(f"Master Volume: {notify_data.fMasterVolume}")
        #         # g_log.info(f"Channel Count: {notify_data.nChannels}")
        #         # g_log.info(f"Channel Volumes: {list(notify_data.afChannelVolumes[:notify_data.nChannels])}")
        
        g_log.info(f"({self.device_type}){self.device_name}: Muted:{notify_data.bMuted} Volume: {notify_data.fMasterVolume * 100:.0f}%")

        if self.device_id == self.audio_manager.device_change_client.defaultInputDeviceID:
            self.TPClient.stateUpdate(PLUGIN_ID + f".state.currentInputMasterVolume", str(master_volume))
            self.TPClient.stateUpdate(PLUGIN_ID + f".state.currentInputMasterVolumeMute", "Muted" if notify_data.bMuted == 1 else "Un-muted")
            self.audio_manager.update_connector(self.device_type.capitalize(), self.device_name, notify_data.fMasterVolume)
            self.audio_manager.update_connector("Input", "Default", notify_data.fMasterVolume)


        elif self.device_id == self.audio_manager.device_change_client.defaultOutputDeviceID:
            self.TPClient.stateUpdate(PLUGIN_ID + f".state.currentMasterVolume", str(master_volume))
            self.TPClient.stateUpdate(PLUGIN_ID + f".state.currentMasterVolumeMute", "Muted" if notify_data.bMuted == 1 else "Un-muted")
            self.audio_manager.update_connector(self.device_type.capitalize(), self.device_name, notify_data.fMasterVolume)
            self.audio_manager.update_connector("Output", "Default", notify_data.fMasterVolume)

        else:
            self.TPClient.stateUpdate(PLUGIN_ID + f".state.device.{self.device_type}.{self.device_name}.volume", str(master_volume))
            self.TPClient.stateUpdate(PLUGIN_ID + f".state.device.{self.device_type}.{self.device_name}.mute", "Muted" if notify_data.bMuted == 1 else "Un-muted")
            self.audio_manager.update_connector(self.device_type.capitalize(), self.device_name, notify_data.fMasterVolume)

    
            
class AudioManager:
    """
    Manages audio devices and their volume callbacks. Handles device registration, 
    unregistration, and notifications for changes in audio devices.

    Attributes:
        devices (dict): Stores devices by ID with their volume and callback.
        device_change_client (Client): Client for handling device change notifications.
        inputDevicesReversed (dict): Stores input devices with device names and IDs.
        outputDevicesReversed (dict): Stores output devices with device names and IDs.

    Methods:
        create_callback_for_device(device, device_type, device_name, device_id):
            Creates and registers a volume callback for a specified device.

        register_single_device(device_id):
            Registers a single device for notifications based on its ID.

        setup_devices(data_flow):
            Sets up devices (input or output) and registers callbacks for them.

        register_all_devices():
            Registers all active input and output devices.

        unregister_all_devices():
            Unregisters all devices and their callbacks.

        unregister_device(device_id):
            Unregisters a specific device by its ID.

        start_listening():
            Starts listening for device changes and sets up notifications.

        stop_listening():
            Stops listening for device changes and unregisters all devices.

        getAllDevices(direction, State):
            Retrieves all devices (input or output) based on the specified direction and state.
    """
    
    def __init__(self, TPClient):
        self.devices = {}  # Store devices by ID (the callbacks)
        self.device_change_client:AudioDeviceNotificationHandler = None
        self.TPClient:TP.Client = TPClient
        
        self.inputDevicesReversed = {}
        self.outputDevicesReversed = {}

    
    def update_connector(self, device_type, device_name, master_volume):
        """
        Update the connector state for a specific device.

        Parameters:
        device_type (str): The type of the device (e.g., 'Output', 'Input').
        device_name (str): The name of the device.
        master_volume (float): The master volume level of the device.
        """
        other_device_connector_id = (
            f"pc_{TP_PLUGIN_INFO['id']}_"
            f"{TP_PLUGIN_CONNECTORS['Device Volume Slider']['id']}|"
            f"{TP_PLUGIN_CONNECTORS['Device Volume Slider']['data']['deviceType']['id']}={device_type}|"
            f"{TP_PLUGIN_CONNECTORS['Device Volume Slider']['data']['deviceOption']['id']}={device_name}"
        )

        if other_device_connector_shortId := self.TPClient.shortIdTracker.get(other_device_connector_id, None):
            self.TPClient.shortIdUpdate(
                other_device_connector_shortId,
                master_volume * 100  
            )
            
    def create_callback_for_device(self, device, device_type, device_name, device_id):
        try:
            interface = device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = interface.QueryInterface(IAudioEndpointVolume)
            callback = AudioEndpointVolumeCallback(device_type, device_name, device_id, self, self.TPClient)
            volume.RegisterControlChangeNotify(callback)
            
            current_volume = volume.GetMasterVolumeLevelScalar()
            current_mute = volume.GetMute()
            
            if device_type == "input":
                self.TPClient.createState(PLUGIN_ID + f".state.device.{device_type}.{device_name}.volume", f"{device_type} - {device_name} Volume", str(round(current_volume * 100)), "Input Devices")
                self.TPClient.createState(PLUGIN_ID + f".state.device.{device_type}.{device_name}.mute", f"{device_type} - {device_name} Mute",  "Muted" if current_mute == 1 else "Un-muted", "Input Devices")
            elif device_type =="output":
                self.TPClient.createState(PLUGIN_ID + f".state.device.{device_type}.{device_name}.volume", f"{device_type} - {device_name} Volume", str(round(current_volume * 100)), "Output Devices")
                self.TPClient.createState(PLUGIN_ID + f".state.device.{device_type}.{device_name}.mute", f"{device_type} - {device_name} Mute",  "Muted" if current_mute == 1 else "Un-muted", "Output Devices")
            
            self.update_connector(device_type.capitalize(), device_name, current_volume)
            return volume, callback
        except Exception as e:
            g_log.info(f"Error creating callback for device {device.GetId()}: {e}")
            return None, None

    def register_single_device(self, device_id):
        pythoncom.CoInitialize()
        try:
            enumerator = AudioUtilities.GetDeviceEnumerator()

            for data_flow in [EDataFlow.eRender, EDataFlow.eCapture]:
                devices = enumerator.EnumAudioEndpoints(data_flow.value, DEVICE_STATE.ACTIVE.value)
                for i in range(devices.GetCount()):
                    device = devices.Item(i)
                    if device.GetId() == device_id:
                        volume, callback = self.create_callback_for_device(device, "output" if data_flow == EDataFlow.eRender else "input")
                        if volume and callback:
                            self.devices[device_id] = (volume, callback)
                            g_log.info(f"Callback registered for {'output' if data_flow == EDataFlow.eRender else 'input'} device: {device_id}")
                        return
            g_log.info(f"Device with ID {device_id} not found.")
        except Exception as e:
            g_log.error(e)
        finally:
            pythoncom.CoUninitialize()
        
        
    def setup_devices(self, data_flow):
        pythoncom.CoInitialize()
        
        try:
            enumerator = AudioUtilities.GetDeviceEnumerator()

            try:
                devices = enumerator.EnumAudioEndpoints(data_flow.value, DEVICE_STATE.ACTIVE.value)
            except Exception as e:
                g_log.info(f"Error enumerating audio endpoints: {e}")
                return []

            device_list = []

            for i in range(devices.GetCount()):
                try:
                    device = devices.Item(i)
                    device_id = device.GetId()
                    state = device.GetState()

                    g_log.info(f"Device ID: {device_id}, State: {state}")

                    if state == DEVICE_STATE.ACTIVE.value:
                        if data_flow == EDataFlow.eRender:
                            device_name = self.outputDevicesReversed.get(device_id, "None")
                            volume, callback = self.create_callback_for_device(device, "output", device_name, device_id)
                            if volume and callback:
                                device_list.append((device_id, volume, callback))
                                g_log.info(f"Callback registered for 'output' device: {device_name} {device_id}")
                        
                        elif data_flow == EDataFlow.eCapture:
                            device_name = self.inputDevicesReversed.get(device_id, "None")
                            volume, callback = self.create_callback_for_device(device, "input", device_name, device_id)
                            if volume and callback:
                                device_list.append((device_id, volume, callback))
                                g_log.info(f"Callback registered for 'input' device: {device_name} {device_id}")

                except Exception as e:
                    g_log.info(f"Error processing device: {e}")
        except Exception as e:
            g_log.info(f"Error processing device: {e}")
        finally:
            pythoncom.CoUninitialize()
            
        return device_list

    def register_all_devices(self):
        self.unregister_all_devices()
        self.devices = {}
        self.devices.update({device_id: (volume, callback) for device_id, volume, callback in self.setup_devices(EDataFlow.eRender)})
        self.devices.update({device_id: (volume, callback) for device_id, volume, callback in self.setup_devices(EDataFlow.eCapture)})

    def unregister_all_devices(self):
        for volume, callback in self.devices.values():
            volume.UnregisterControlChangeNotify(callback)
        self.devices = {}

    def unregister_device(self, device_id):
        if device_id in self.devices:
            volume, callback = self.devices.pop(device_id)
            volume.UnregisterControlChangeNotify(callback)
            g_log.info(f"Callback unregistered for device: {device_id}")
        else:
            g_log.info(f"Device with ID {device_id} not registered.")

    def start_listening(self):

        self.register_all_devices()

        # Set up device change notification
        self.device_change_client = AudioDeviceNotificationHandler(self.register_all_devices, self, self.TPClient)
        enumerator = AudioUtilities.GetDeviceEnumerator()
        enumerator.RegisterEndpointNotificationCallback(self.device_change_client)
        
        self.initialize_default_devices()
        # return self.device_change_client

    def stop_listening(self):
        enumerator = AudioUtilities.GetDeviceEnumerator()
        if self.device_change_client:
            enumerator.UnregisterEndpointNotificationCallback(self.device_change_client)
        self.unregister_all_devices()
    
    def fetch_devices(self):
        """ Returns inputDevicesReversed, outputDevicesReversed"""
        self.outputDevices = audioSwitch.MyAudioUtilities.getAllDevices(direction="output")
        self.inputDevices  = audioSwitch.MyAudioUtilities.getAllDevices(direction="input")
        
        self.outputDevicesReversed = {v: k for k, v in self.outputDevices.items()} 
        self.inputDevicesReversed = {v: k for k, v in self.inputDevices.items()}
        return self.inputDevicesReversed.keys(), self.outputDevicesReversed.keys()
        
    def get_device_by_name(self, name, device_type):
        """Retrieve the volume object for the selected device
        - returns volume object, deviceid
        """
        if device_type == "Output":
            if name == "Default":
                deviceid = self.device_change_client.defaultOutputDeviceID
                volume, _ = self.devices.get(deviceid, (None, None))
            else:
                deviceid = self.outputDevices.get(name)
                volume, _ = self.devices.get(deviceid, (None, None))

        if device_type == "Input":
            if name == "Default": 
                deviceid = self.device_change_client.defaultInputDeviceID
                volume, _ = self.devices.get(deviceid, (None, None))
            else:
                deviceid = self.inputDevices.get(name)
                volume, _ = self.devices.get(deviceid, (None, None))

        return volume, deviceid
 
 
    def initialize_default_devices(self):
        """ 
        When starting up we fetch the default input/output devices 
        Should be event based after that.
        """
        device_map = {
            "outputDevice": {
                "edata": EDataFlow.eRender.value,
                "erole": ERole.eMultimedia.value
            },
            "outputCommunicationDevice": {
                "edata": EDataFlow.eRender.value,
                "erole": ERole.eCommunications.value
            },
            "inputDevice": {
                "edata": EDataFlow.eCapture.value,
                "erole": ERole.eMultimedia.value
            },
            "inputCommunicationDevice": {
                "edata": EDataFlow.eCapture.value,
                "erole": ERole.eCommunications.value
            }
        }
        statelist = []
            
        def get_default_device_id(edata, erole):
            """Helper function to get device ID from device type and role."""
            
            ## We could probably just use getDeviceByData and modify it to send us the ID aswlel?
            device_enumerator = comtypes.CoCreateInstance(
                CLSID_MMDeviceEnumerator,
                IMMDeviceEnumerator,
                comtypes.CLSCTX_INPROC_SERVER
            )
            default_device = device_enumerator.GetDefaultAudioEndpoint(edata, erole)
            return default_device.GetId() if default_device else None

        try:
            # Set the device IDs directly
            self.device_change_client.defaultOutputDeviceID = get_default_device_id(device_map['outputDevice']['edata'], device_map['outputDevice']['erole'])
            self.device_change_client.defaultOutputCommunicationDeviceID = get_default_device_id(device_map['outputCommunicationDevice']['edata'], device_map['outputCommunicationDevice']['erole'])
            self.device_change_client.defaultInputDeviceID = get_default_device_id(device_map['inputDevice']['edata'], device_map['inputDevice']['erole'])
            self.device_change_client.defaultInputCommunicationDeviceID = get_default_device_id(device_map['inputCommunicationDevice']['edata'], device_map['inputCommunicationDevice']['erole'])
            
            statelist.extend([
            { "id": TP_PLUGIN_STATES["outputDevice"]["id"], "value": self.outputDevicesReversed.get(self.device_change_client.defaultOutputDeviceID, "Unknown")},
            { "id": TP_PLUGIN_STATES["outputDeviceCommunication"]["id"], "value": self.outputDevicesReversed.get(self.device_change_client.defaultOutputCommunicationDeviceID, "Unknown")},
            { "id": TP_PLUGIN_STATES["inputDevice"]["id"], "value": self.inputDevicesReversed.get(self.device_change_client.defaultInputDeviceID, "Unknown")},
            { "id": TP_PLUGIN_STATES["inputDeviceCommunication"]["id"], "value": self.inputDevicesReversed.get(self.device_change_client.defaultInputCommunicationDeviceID, "Unknown")}
            ])

                # Update connectors for each device individually
            if self.device_change_client.defaultOutputDeviceID:
                device_name = self.outputDevicesReversed.get(self.device_change_client.defaultOutputDeviceID, "Unknown")
                device, _ = self.devices[self.device_change_client.defaultOutputDeviceID]
                if device:
                    master_volume = device.GetMasterVolumeLevelScalar()
                    muted = device.GetMute()
                    statelist.extend([
                        {"id": PLUGIN_ID + f".state.currentMasterVolume", "value": str(round(master_volume * 100)) },
                        {"id": PLUGIN_ID + f".state.currentMasterVolumeMute", "value": "Muted" if muted == 1 else "Un-muted"}
                    ])
                    self.update_connector("Output", 'Default', master_volume)

            if self.device_change_client.defaultInputDeviceID:
                device_name = self.inputDevicesReversed.get(self.device_change_client.defaultInputDeviceID, "Unknown")
                device, _ = self.devices[self.device_change_client.defaultInputDeviceID]
                if device:
                    master_volume = device.GetMasterVolumeLevelScalar()
                    muted = device.GetMute()
                    statelist.extend([
                        {"id": PLUGIN_ID + f".state.currentInputMasterVolume", "value": str(round(master_volume * 100)) },
                        {"id": PLUGIN_ID + f".state.currentInputMasterVolumeMute", "value": "Muted" if muted == 1 else "Un-muted"}
                    ])
                    self.update_connector("Input", "Default", device.GetMasterVolumeLevelScalar())
        
            self.TPClient.stateUpdateMany(statelist)
            # Log the device IDs
            g_log.info(f"Default output device ID: {self.device_change_client.defaultOutputDeviceID}")
            g_log.info(f"Default output communication device ID: {self.device_change_client.defaultOutputCommunicationDeviceID}")
            g_log.info(f"Default input device ID: {self.device_change_client.defaultInputDeviceID}")
            g_log.info(f"Default input communication device ID: {self.device_change_client.defaultInputCommunicationDeviceID}")
        except Exception as e:
            g_log.info(f"Error initializing default devices: {e}")

    


class AudioDeviceNotificationHandler(MMNotificationClient):
    """
    Handles audio device notifications such as default device changes,
    device state changes, and property value changes.
    - could handle new device connects/disconnects and other things as well
    """
    def __init__(self, setup_default_device_callback, audio_manager:AudioManager, tpClient:TP.Client):
        """
        Initializes the Client with a callback for default device changes.
        """
        super().__init__()
        self.setup_default_device = setup_default_device_callback
        self.audio_manager = audio_manager
        self.TPClient = tpClient
        self.defaultOutputDeviceID = None
        self.defaultOutputCommunicationDeviceID = None
        
        self.defaultInputDeviceID = None
        self.defaultInputCommunicationDeviceID = None

    def OnDefaultDeviceChanged(self, flow, role, pwstrDeviceId):
        g_log.info(f"Default device changed: flow={flow}, role={role}, device_id={pwstrDeviceId}")    
            
        ## if its output
        if flow == EDataFlow.eRender.value:
            if role == ERole.eCommunications.value:
                self.defaultOutputCommunicationDeviceID  = pwstrDeviceId
                self.TPClient.stateUpdate(TP_PLUGIN_STATES["outputDeviceCommunication"]["id"], self.audio_manager.outputDevicesReversed.get(self.defaultOutputCommunicationDeviceID, "Unknown"))
            else:
                self.defaultOutputDeviceID = pwstrDeviceId
                self.TPClient.stateUpdate(TP_PLUGIN_STATES["outputDevice"]["id"], self.audio_manager.outputDevicesReversed.get(self.defaultOutputDeviceID, "Unknown"))
        
        elif flow == EDataFlow.eCapture.value:
            if role == ERole.eCommunications.value:
                self.defaultInputCommunicationDeviceID = pwstrDeviceId
                self.TPClient.stateUpdate(TP_PLUGIN_STATES["inputDeviceCommunication"]["id"], self.audio_manager.inputDevicesReversed.get(self.defaultInputCommunicationDeviceID, "Unknown"))
            else:
                self.defaultInputDeviceID = pwstrDeviceId
                self.TPClient.stateUpdate(TP_PLUGIN_STATES["inputDevice"]["id"], self.audio_manager.inputDevicesReversed.get(self.defaultInputDeviceID, "Unknown"))
        
        ## starting new new listeners for the new default device
        if flow == EDataFlow.eRender.value or flow == EDataFlow.eCapture.value:
            threading.Thread(target=self.setup_default_device).start()

    def OnDeviceStateChanged(self, pwstrDeviceId, dwNewState):
        g_log.debug(f"Device state changed: {pwstrDeviceId} {dwNewState}")

    def OnPropertyValueChanged(self, pwstrDeviceId, key):
        g_log.debug(f"Property value changed: device={pwstrDeviceId} key={key}")

    def OnDeviceAdded(self, added_device_id):
        g_log.debug(f"New Device Found! {added_device_id}")
    
    def OnDeviceRemoved(self, added_device_id):
        g_log.debug(f"Device Removed! {added_device_id}")

    

def main():
    # global audio_manager
    audio_manager = AudioManager()
    # Obtain a list of all devices
    audio_manager.outputDevicesReversed = audio_manager.getAllDevices(direction="output")
    audio_manager.inputDevicesReversed = audio_manager.getAllDevices(direction="input")
    
    outputDevicesReversed = {v: k for k, v in audio_manager.outputDevicesReversed.items()} 
    inputDevicesReversed = {v: k for k, v in audio_manager.inputDevicesReversed.items()} 
    
    audio_manager.outputDevicesReversed = outputDevicesReversed
    audio_manager.inputDevicesReversed = inputDevicesReversed

    try:
        audio_manager.start_listening()
        g_log.info("Listening for volume and device changes... Press Ctrl+C to exit.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        g_log.info("Exiting...")
    finally:
        audio_manager.stop_listening()

if __name__ == "__main__":
    main()

