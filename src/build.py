"""
In order for buildScript to work, you need to have the following variables in your build file:

    - PLUGIN_ROOT: (Required)
        This lets the build script to know your plugin's root directory.

    - OUTPUT_PATH: (Required)
        This tells tppbuild where you want finished build tpp to be saved at. Default "./" meaning current dir where tppbuild is running from.


    - PLUGIN_MAIN: (Required)
        This lets tppbuild know where your main python plugin file is located so it will know which file to compile.

    - PLUGIN_EXE_NAME: (Required)
        This is the name of the executable file that is compiled by Pyinstaller.

    - PLUGIN_EXE_ICON: (Optional)
        This should be a path to a .ico file. However if png passed in, it will automatically converted to ico.
        Otherwise, it will use pyinstaller's default icon.


    - PLUGIN_ENTRY: (Required)
        This can be either path to entry.tp or path to a python file that contains infomation about entry.
        Note if you pass in a entry.tp, tppbuild will automatically validate the json. If you pass in a python file, it will
        build entry.tp & validate it for you. If validation fails, tppbuild will exit.

    - PLUGIN_ENTRY_INDENT: (Required)
        Indent level (spaces) for generated JSON. Use 0 for only newlines, or -1 for the most compact representation. Default is 2 spaces.

    - PLUGIN_VERSION: (Required)
        A version string will be used as part of .tpp file.


    - ADDITIONAL_FILES: (Optional)
        If your plugin requires any additional files for your plugin to work, you can add them here.

    - ADDITIONAL_PYINSTALLER_ARGS: (Optional)
        If you have additional arguments for Pyinstaller, you can add them here. otherwise default it will use these arguments:
        '--onefile', '--noconsole', '--distpath', 'dist', 'name', 'icon'

Even if you don't use all of the above variables, you still need to have the following variables in your build file

"""

from TouchPortalAPI import tppbuild

"""
PLUGIN_MAIN: This lets tppbuild know where your main python plugin file is located so it will know which file to compile.
"""
PLUGIN_MAIN = "TPAudioMixer.py"

"""
PLUGIN_EXE_NAME: This defines what you want your plugin executable to be named. tppbuild will also use this for the .tpp file in the format:
                `pluginname + "_v" + version + "_" + os_name + ".tpp"`
                If left blank, the file name from PLUGIN_MAIN is used (w/out .py extension).
"""
PLUGIN_EXE_NAME = "TPAudioMixer"

"""
PLUGIN_EXE_ICON: This should be a path to a .ico file. However if png passed in, it will automatically converted to ico.
"""
PLUGIN_EXE_ICON = "icon.ico"


"""
PLUGIN_ENTRY: This can be either path to entry.tp or path to a python file that contains infomation about entry.
Note if you pass in a entry.tp, tppbuild will automatically validate the json. If you pass in a python file, it will
build entry.tp & validate it for you. If validation fails, tppbuild will exit.
"""
PLUGIN_ENTRY = "tppEntry.py"  # Here we just use the same file as the plugin's main code since that contains all the definitions for entry.tp.

"""

"""
PLUGIN_ENTRY_INDENT = -1

""" This is the root folder name that will be inside of .tpp """
PLUGIN_ROOT = "TouchPortalMediaMixer"

""" Path to icon file used in entry.tp for category `imagepath`, if any. If left blank, TP will use a default icon. """
PLUGIN_ICON = r"icon.png"

""" This tells tppbuild where you want finished build tpp to be saved at. Default "./" meaning current dir where tppbuild is running from. """
OUTPUT_PATH = r"../"

""" PLUGIN_VERSION: A version string for the generated .tpp file name. This example reads the `__version__` from the example plugin's code. """
from tppEntry import __version__
PLUGIN_VERSION = __version__

# Or just set the PLUGIN_VERSION manually.
# PLUGIN_VERSION = "1.0.0-beta1"

"""
If you have any required file(s) that your plugin needs, put them in this list.
"""
ADDITIONAL_FILES = [
    "start.bat",
    "AudioDLL.dll"
]

"""
Any additional arguments to be passed to Pyinstaller. Optional.
"""
ADDITIONAL_PYINSTALLER_ARGS = [
    "--log-level=WARN"
]

ADDITIONAL_TPPSDK_ARGS = []
ADDITINAL_TPPSDK_ARGS  = ADDITIONAL_TPPSDK_ARGS

if __name__ == "__main__":
    tppbuild.validateBuild()
    tppbuild.runBuild()
