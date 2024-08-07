__version__ = 200

PLUGIN_ID = "com.github.KillerBOSS2019.WinMediaMixer"

TP_PLUGIN_INFO = {
    'sdk': 6,
    'version': __version__,
    'name': "TouchPortal Windows Media Mixer",
    'id': PLUGIN_ID,
    'plugin_start_cmd': "%TP_PLUGIN_FOLDER%TouchPortalMediaMixer\\TPAudioMixer.exe",
    'configuration': {
        'colorDark': "#6c6f73",
        'colorLight': "#3d62ad"
    },
    'doc': {
        "description": "Control Windows Media for Audio Devices and Applications",
        "repository": "KillerBOSS2019:TouchPortal-Windows-MediaMixer",
        "Install": "1. Download .tpp file\n2. in TouchPortal gui click gear icon and select 'Import Plugin'\n3. Select the .tpp file\n4. Click 'Import'",
    }
}

TP_PLUGIN_SETTINGS = {
    'ignore list': {
        'name': "Audio process ignore list",
        'type': "text",
        'default': "Enter '.exe' name seperated by a comma for more then 1",
        'readOnly': False,
        'value': None,
        "doc": "A list of processes to ignore when searching for audio processes. This is useful if you have a process that is not an audio process, but is still playing audio. You can add the name of the process to this list and Touch Portal will ignore it when searching for audio processes."
    },
}

TP_PLUGIN_CATEGORIES = {
    "main": {
        'id': PLUGIN_ID + ".main",
        'name' : "Windows Media Mixer",
        'imagepath' : "%TP_PLUGIN_FOLDER%TouchPortalMediaMixer\\icon.png"
    },
    "Default Input Devices": {
        'id': PLUGIN_ID + ".inputDevices",
        'name' : "Default Input Devices",
        'imagepath' : "%TP_PLUGIN_FOLDER%TouchPortalMediaMixer\\icon.png"
    },
    "Default Output Devices": {
        'id': PLUGIN_ID + ".outputDevices",
        'name' : "Default Output Devices",
        'imagepath' : "%TP_PLUGIN_FOLDER%TouchPortalMediaMixer\\icon.png"
    },
    "Focused App": {
        'id': PLUGIN_ID + ".focusedApp",
        'name' : "Current Focused App",
        'imagepath' : "%TP_PLUGIN_FOLDER%TouchPortalMediaMixer\\icon.png"
    },
}

TP_PLUGIN_CONNECTORS = {
    "APP Volume Slider": {
        'category': "main",
        "id": PLUGIN_ID + ".connector.APPcontrol",
        "name": "Volume Mixer: APP Volume slider",
        "format": "Control volume for $[1]",
        "label": "control app Volume",
        "data": {
            "appchoice": {
                "id": PLUGIN_ID + ".connector.APPcontrol.data.slidercontrol",
                "type": "choice",
                "label": "APP choice list for APP Volume slider",
                "default": "",
                "valueChoices": []
            }
        }
    },
    "Device Volume Slider": {
        'category': "main",
        "id": PLUGIN_ID + ".connector.WinAudio",
        "name": "Volume Mixer: Windows Volume slider",
        "format": "Control Device Volume $[1] device$[2]",
        "label": "control windows Volume",
        "data": {
            'deviceType': {
                'id': PLUGIN_ID + ".connector.WinAudio.deviceType",
                'type': "choice",
                'label': "device type",
                'default': "Pick One",
                "valueChoices": [
                    "Output",
                    "Input"
                ]
            },
            'deviceOption': {
                'id': PLUGIN_ID + ".connector.WinAudio.devices",
                'type': "choice",
                'label': "Device choice list",
                'default': "",
                "valueChoices": []
            },
        }
    }
}

TP_PLUGIN_ACTIONS = {
    'AppMute': {
        'category': "main",
        'id': PLUGIN_ID + ".act.Mute/Unmute",
        'name': 'Mute/Unmute process volume',
        'prefix': TP_PLUGIN_CATEGORIES['main']['name'],
        'type': "communicate",
        'tryInline': True,
        'format': "$[1]$[2]app",
        "doc": "Mute/Unmute process volume",
        'data': {
            'appChoice': {
                'id': PLUGIN_ID + ".act.Mute/Unmute.data.process",
                'type': "choice",
                'label': "process list",
                'default': "",
                "valueChoices": []
                
            },
            'OptionList': {
                'id': PLUGIN_ID + ".act.Mute/Unmute.data.choice",
                'type': "choice",
                'label': "Option choice",
                'default': "Toggle",
                "valueChoices": [
                    "Mute",
                    "Unmute",
                    "Toggle"
                ]
            },
        }
    },
    'Inc/DecrVol': {
        'category': "main",
        'id': PLUGIN_ID + ".act.Inc/DecrVol",
        'name': 'Adjust App Volume',
        'prefix': TP_PLUGIN_CATEGORIES['main']['name'],
        'type': "communicate",
        'tryInline': True,
        'format': "$[2]$[1]volume$[3]",
        "doc": "Increase/Decrease process volume",
        "hasHoldFunctionality": True,
        'data': {
            'AppChoice': {
                'id': PLUGIN_ID + ".act.Inc/DecrVol.data.process",
                'type': "choice",
                'label': "process list",
                'default': "",
                "valueChoices": []
                
            },
            'OptionList': {
                'id': PLUGIN_ID + ".act.Inc/DecrVol.data.choice",
                'type': "choice",
                'label': "Option choice",
                'default': "Increase",
                "valueChoices": [
                    "Increase",
                    "Decrease",
                    "Set"
                ]
            },
            'Volume': {
                'id': PLUGIN_ID + ".act.Inc/DecrVol.data.Volume",
                'type': "text",
                'label': "Volume",
                "default": "10"
            },
        }
    },
    'ChangeOut/Input': {
        'category': "main",
        'id': PLUGIN_ID + ".act.ChangeAudioOutput",
        'name': 'Audio Output/Input Device Switcher',
        'prefix': TP_PLUGIN_CATEGORIES['main']['name'],
        'type': "communicate",
        'tryInline': True,
        'format': "Change audio device$[1]$[2]$[3]",
        "doc": "Change Default Audio Devices",
        'data': {
            'optionSel': {
                'id': PLUGIN_ID + ".act.ChangeAudioOutput.choice",
                'type': "choice",
                'label': "process list",
                'default': "Pick One",
                "valueChoices": [
                    "Output",
                    "Input"
                ]
                
            },
            'deviceOption': {
                'id': PLUGIN_ID + ".act.ChangeAudioOutput.data.device",
                'type': "choice",
                'label': "Device choice list",
                'default': "",
                "valueChoices": []
            },
            'setType': {
                'id': PLUGIN_ID + ".act.ChangeAudioOutput.setType",
                'type': "choice",
                'label': "Set audio device type",
                'default': "Default",
                "valueChoices": [
                    "Default",
                    "Communications"
                ]
                
            },
        }
    },
    'ToggleOut/Input': {
        'category': "main",
        'id': PLUGIN_ID + ".act.ToggleAudioOutput",
        'name': 'Audio Output/Input Device Toggle',
        'prefix': TP_PLUGIN_CATEGORIES['main']['name'],
        'type': "communicate",
        'tryInline': True,
        'format': "Toggle audio device$[1]$[2]$[3]$[4]",
        "doc": "Toggle Default Audio Devices",
        'data': {
            'optionSel': {
                'id': PLUGIN_ID + ".act.ToggleAudioOutput.choice",
                'type': "choice",
                'label': "process list",
                'default': "Pick One",
                "valueChoices": [
                    "Output",
                    "Input"
                ]
            },
            'deviceOption1': {
                'id': PLUGIN_ID + ".act.ToggleAudioOutput.data.device1",
                'type': "choice",
                'label': "Device choice list",
                'default': "",
                "valueChoices": []
            },
            'deviceOption2': {
                'id': PLUGIN_ID + ".act.ToggleAudioOutput.data.device2",
                'type': "choice",
                'label': "Device choice list",
                'default': "",
                "valueChoices": []
            },
            'setType': {
                'id': PLUGIN_ID + ".act.ToggleAudioOutput.setType",
                'type': "choice",
                'label': "Set audio device type",
                'default': "Default",
                "valueChoices": [
                    "Default",
                    "Communications"
                ]
                
            },
        }
    },
    'setDeviceVolume': {
        'category': "main",
        'id': PLUGIN_ID + ".act.changeDeviceVolume",
        'name': 'Set Device Volume',
        'prefix': TP_PLUGIN_CATEGORIES['main']['name'],
        'type': "communicate",
        'tryInline': True,
        'format': "$[4] Volume$[1]device$[2]to$[3]%",
        "hasHoldFunctionality": True,
        "doc": "Change Default Audio Devices",
        'data': {
            'deviceType': {
                'id': PLUGIN_ID + ".act.changeDeviceVolume.deviceType",
                'type': "choice",
                'label': "device type",
                'default': "Pick One",
                "valueChoices": [
                    "Output",
                    "Input"
                ]
            },
            'deviceOption': {
                'id': PLUGIN_ID + ".act.changeDeviceVolume.devices",
                'type': "choice",
                'label': "Device choice list",
                'default': "",
                "valueChoices": []
            },
            'Volume': {
                'id': PLUGIN_ID + ".act.changeDeviceVolume.Volume",
                'type': "text",
                'label': "Volume",
                "default": "10"
            },
            'OptionList': {
                'id': PLUGIN_ID + ".act.changeDeviceVolume.choice",
                'type': "choice",
                'label': "Option choice",
                'default': "Increase",
                "valueChoices": [
                    "Increase",
                    "Decrease",
                    "Set"
                ]
            },
        }
    },
    'setDeviceMute': {
        'category': "main",
        'id': PLUGIN_ID + ".act.changeDeviceMute",
        'name': 'Set Device Mute',
        'prefix': TP_PLUGIN_CATEGORIES['main']['name'],
        'type': "communicate",
        'tryInline': True,
        'format': "Set Mute$[1]device$[2]to$[3]",
        "doc": "Change Default Audio Devices",
        'data': {
            'deviceType': {
                'id': PLUGIN_ID + ".act.changeDeviceMute.deviceType",
                'type': "choice",
                'label': "device type",
                'default': "Pick One",
                "valueChoices": [
                    "Output",
                    "Input"
                ]
            },
            'deviceOption': {
                'id': PLUGIN_ID + ".act.changeDeviceMute.devices",
                'type': "choice",
                'label': "Device choice list",
                'default': "",
                "valueChoices": []
            },
            'muteChoice': {
                'id': PLUGIN_ID + ".act.changeDeviceMute.choices",
                'type': "choice",
                'label': "Volume",
                "default": "Toggle",
                "valueChoices": [
                    "Toggle",
                    "Mute",
                    "Un-Mute"
                ]
            },
        }
    },
    'AppAudioSwitch': {
        'category': "main",
        'id': PLUGIN_ID + ".act.appAudioSwitch",
        'name': 'Individual App Audio Device switcher',
        'prefix': TP_PLUGIN_CATEGORIES['main']['name'],
        'type': "communicate",
        'tryInline': True,
        'format': "Set$[1]$[3]device to$[2]",
        "doc": "Change indivdual app output/input devices.",
        'data': {
            'AppChoice': {
                'id': PLUGIN_ID + ".act.appAudioSwitch.data.process",
                'type': "choice",
                'label': "process list",
                'default': "",
                "valueChoices": []
                
            },
            'devicelist': {
                'id': PLUGIN_ID + ".act.appAudioSwitch.data.devices",
                'type': "choice",
                'label': "Device choice list",
                'default': "",
                "valueChoices": []
            },
            'deviceType': {
                'id': PLUGIN_ID + ".act.ChangeAudioOutput.deviceType",
                'type': "choice",
                'label': "device type",
                'default': "Pick One",
                "valueChoices": [
                    "Output",
                    "Input"
                ]
            }
        }
    }
}

TP_PLUGIN_STATES = {
    'outputDevice': {
        'category': "Default Output Devices",
        'id': PLUGIN_ID + ".state.CurrentOutputDevice",
        'type': "text",
        'desc': "Audio Device: Default Output Device",
        'default': ""
    },
    'outputDeviceCommunication': {
        'category': "Default Output Devices",
        'id': PLUGIN_ID + ".state.CurrentOutputCommicationDevice",
        'type': "text",
        'desc': "Audio Device: Default Output Communications Device",
        'default': ""
    },
    'inputDevice': {
        'category': "Default Input Devices",
        'id': PLUGIN_ID + ".state.CurrentInputDevice",
        'type': "text",
        'desc': "Audio Device: Default Input Device",
        'default': ""
    },
    'inputDeviceCommunication': {
        'category': "Default Input Devices",
        'id': PLUGIN_ID + ".state.CurrentInputCommucationDevice",
        'type': "text",
        'desc': "Audio Device: Default Input Communications Device",
        'default': ""
    },
    'master volume': {
        'category': "Default Output Devices",
        'id': PLUGIN_ID + ".state.currentMasterVolume",
        'type': "text",
        'desc': "Volume Mixer: Master Output Volume",
        'default': ""
    },
    'master volume mute': {
        'category': "Default Output Devices",
        'id': PLUGIN_ID + ".state.currentMasterVolumeMute",
        'type': "text",
        'desc': "Volume Mixer: Master Output Volume Mute",
        'default': ""
    },
    'master volume input': {
        'category': "Default Input Devices",
        'id': PLUGIN_ID + ".state.currentInputMasterVolume",
        'type': "text",
        'desc': "Volume Mixer: Master Input Volume",
        'default': ""
    },
    'master volume input mute': {
        'category': "Default Input Devices",
        'id': PLUGIN_ID + ".state.currentInputMasterVolumeMute",
        'type': "text",
        'desc': "Volume Mixer: Master Input Volume Mute",
        'default': ""
    },
    'FocusedAPP': {
        'category': "Focused App",
        'id': PLUGIN_ID + ".state.currentFocusedAPP",
        'type': "text",
        'desc': "Volume Mixer: Current Focused App",
        'default': ""
    },
    'currentAppVolume': {
        'category': "Focused App",
        'id': PLUGIN_ID + ".state.currentAppVolume",
        'type': "text",
        "desc": "Volume Mixer: Current Focused App volume",
        "default": ""
    },
    'currentAppMute': {
        'category': "Focused App",
        'id': PLUGIN_ID + ".state.currentAppMute",
        'type': "text",
        "desc": "Volume Mixer: Current Focused App Mute",
        "default": ""
    },
}