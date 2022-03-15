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
from distutils.command.config import config
from setuptools import setup
from setuptools.command.install import install
from setuptools.command.develop import develop
from setuptools.command.egg_info import egg_info
import pathlib

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

from osidle.version import VERSION

data_files=[
  # Copy the base configuration file to the global folder
  ('/etc', ['etc/osidled.conf']),
  ('/etc/default', ['etc/osidled.conf']),
  # Prepare the service configuration file
  ('/etc/systemd/system', ['etc/systemd/system/osidled.service']),
  # Make sure that the working folder for the service is created
  ('/var/lib/osidled/', [])             
]

if __name__ == "__main__":
  import os
  import shutil
  import sys
  import argparse

  parser = argparse.ArgumentParser(description='osidle setup', allow_abbrev=False)
  parser.add_argument('--overwrite-config', dest="overwrite_config", action='store_true', help='Overwrite the configuration files if exist', default=False)
  args, unkown = parser.parse_known_args()
  overwriteconfig = False
  if args.overwrite_config:
    sys.argv.remove('--overwrite-config')
    overwriteconfig = True

  def copyfiles():
    global data_files, overwriteconfig
    for folder, files in data_files:
      if not os.path.exists(folder):
        os.makedirs(folder)
      if not os.path.isdir(folder):
        raise Exception("Error: {} is not a directory\n".format(folder))
      for file in files:
        configfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), file)
        if os.path.isdir(configfile):
          print("es un directorio")
          # It is a folder... so copy recursively
          if overwriteconfig or not os.path.exists(os.path.join(folder, file)):
            shutil.copytree(configfile, folder)
          pass
        elif os.path.isfile(configfile):
          # It is a file... so copy it
          if overwriteconfig or (not os.path.exists(os.path.join(folder, os.path.basename(file)))):
            shutil.copy2(configfile, folder)
        else:
          raise Exception("Error: could not find file {}\n".format(file))            

  class PostInstallCommand(install):
    def run(self):
      super().run()
      copyfiles()

  class PostDevelopCommand(develop):
    def run(self):
      super().run()
      copyfiles()

  class PostEggCommand(egg_info):
    def run(self):
      super().run()

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
    cmdclass={
        'install': PostInstallCommand,
        'develop': PostDevelopCommand,
        'egg_info': PostEggCommand,
    },
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
        'osidle-packdb=osidle.packdb:osidle_packdb',
      ]
    },
    # data_files=data_files
  )

