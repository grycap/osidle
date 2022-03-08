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
from setuptools import setup
import pathlib

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

from osidle.version import VERSION

setup(
  name = 'osidle',            
  packages = ['osidle'],
  version = VERSION,          
  license='Apache 2.0',                   # Chose a license from here: https://help.github.com/articles/licensing-a-repository
  description = 'A system that gathers information for the usage of resources of the VMs in OpenStack, to try to detect which of them are idle',
  long_description = README,
  long_description_content_type = 'text/markdown',
  author = 'Carlos A.',             
  author_email = 'caralla@upv.es',  
  url = 'https://github.com/dealfonso/osidle',
  keywords = ['openstack', 'idle', 'virtual machine' ],
  install_requires=[
          'dateutils',
          'requests',
          'tqdm',
          'xlsxwriter'
      ],
  classifiers=[
    'Development Status :: 4 - Beta',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
    'Intended Audience :: System Administrators',
    'Topic :: Utilities',
    'License :: OSI Approved :: Apache Software License',
    'Programming Language :: Python :: 3',
  ],
  entry_points = {
    'console_scripts' : [
      'osidle=osidle.analysis:osidle_analysis',
      'osidled=osidle.monitor:osidle_monitor',
    ]
  },
  data_files=[
    # Copy the base configuration file to the global folder
    ('/etc', ['etc/osidled.conf']),
    # Prepare the service configuration file
    ('/etc/systemd/system', ['etc/systemd/system/osidled.service']),
    # Make sure that the working folder for the service is created
    ('/var/lib/osidled/', [])             
  ]
)