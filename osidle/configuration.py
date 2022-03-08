#
#    Copyright 2022 - Carlos A. <https://github.com/dealfonso>
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#
import configparser
import os
from .common import p_error, p_warning

class Configuration:
    def __init__(self, defaultvalues = {}):
        self._defaultvalues = defaultvalues
        self._reader = configparser.ConfigParser()

    def read(self, filename, onlyfirst = False, allownodefault = False):
        filesread = []

        # if filename is not an array, convert it to an array
        if not isinstance(filename, list):
            filename = [ filename ]
        
        # read the configuration files but if onlyfirst is True, only the first one is read
        for _filename in filename:
            if os.path.isfile(_filename):
                self._reader.read(_filename)
                filesread.append(_filename)
                if onlyfirst:
                    break

        # Check the different keys in the default values and convert the obtained values to the same type
        _result = {}
        for section, secconfig in self._defaultvalues.items():
            if section not in self._reader:
                continue
            if section not in _result:
                _result[section] = {}
            readconfig = self._reader[section]
            for key in secconfig:

                # If it is not a tuple, convert it to a tuple
                if not isinstance(secconfig[key], tuple) or isinstance(secconfig[key], list):
                    secconfig[key] = (secconfig[key], lambda x: x)

                # Get the values of the tuple
                the_default = secconfig[key][0]
                the_type = type(the_default)
                the_function = secconfig[key][1]
                if not callable(the_function):
                    the_type = the_function
                    the_function = lambda x: x

                    # If there is an additional parameter, it should be the function
                    if len(secconfig[key]) > 2:
                        the_function = secconfig[key][2]

                # Make a last check to see if the function is callable
                if not callable(the_function):
                    p_warning("The third parameter of the tuple should be a function; ignoring it")
                    the_function = lambda x: x

                # If the key is in the configuration file, extract it, using the same type as the default value
                if key in readconfig:
                    try:
                        if the_type == bool:
                            _result[section][key] = readconfig.getboolean(key, the_default)
                        elif the_type == int:
                            _result[section][key] = readconfig.getint(key, the_default)
                        elif the_type == float:
                            _result[section][key] = readconfig.getfloat(key, the_default)
                        else:
                            _result[section][key] = readconfig.get(key, the_default)
                    except ValueError:
                        p_error("invalid value for {} in {}".format(key, _filename))
                        _result[section][key] = secconfig[key]
                else:
                    _result[section][key] = the_default

                # Now call the function to correct the value
                _result[section][key] = the_function(_result[section][key])

        if allownodefault:
            # Check the values in the configuration file and if there is no a default value, get it from the configuration file
            for section, readconfig in self._reader.items():
                if section not in _result:
                    _result[section] = {}
                for key in readconfig:
                    if key not in _result[section]:
                        _result[section][key] = readconfig[key]

        return (filesread, _result)