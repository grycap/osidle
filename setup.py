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

# The data files to be installed. The syntax is the same as for the setup(), but in this version
#   it is possible to chown the files and to force overwritting or not:
#   ( "destination folder", [ "list of relative filenames or folders to be copied to the destination folder", "user:group" to chown, True/False to force overwritting ] )
#   - The user:group can be set to "" to not to chown the files, or omit any of them to not to chown the group or the user
data_files=[
  # Copy the base configuration file to the global folder
  ('/etc/osidled/', ['etc/osidled.conf'], "", False),
  ('/etc/osidled/', ['etc/osidle-notify'], "", True),
  ('/etc/default', ['etc/osidled.conf'], "", True),
  # Prepare the service configuration file
  ('/etc/systemd/system', ['etc/systemd/system/osidled.service'], "", True),
  # Make sure that the working folder for the service is created
  ('/var/lib/osidled/', [], "", False),
]

def chown(path, user, recursive=False):
  if user == "":
    return

  user_p = user.split(":")
  user = user_p[0] if user_p[0] != "" else None
  group = user_p[1] if len(user_p) > 1 else None

  import pwd
  import grp

  try:
    uid = pwd.getpwnam(user).pw_uid
  except KeyError:
    uid = None
  
  try:
    gid = grp.getgrnam(group).gr_gid
  except KeyError:
    gid = None

  try:
    if not recursive or os.path.isfile(path):
      shutil.chown(path, user, group)
    else:
      for root, dirs, files in os.walk(path):
        shutil.chown(root, user, group)
        for item in dirs:
          shutil.chown(os.path.join(root, item), user, group)
        for item in files:
          shutil.chown(os.path.join(root, item), user, group)
  except OSError as e:
    raise e 

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
    for options in data_files:
      if len(options) < 2:
        raise Exception("Invalid data file options")
      if len(options) < 3:
        options = [ *options, "" ]
      if len(options) < 4:
        options = [ *options, False ]
      [ folder, files, user, forceoverwrite ] = options
      # Get the user to change the ownership of the files
      # Create the folder if it does not exist
      if not os.path.exists(folder):
        os.makedirs(folder)
        chown(folder, user, recursive=False)
      if not os.path.isdir(folder):
        raise Exception("Error: {} is not a directory\n".format(folder))
      for file in files:
        configfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), file)
        if os.path.isdir(configfile):
          # It is a folder... so copy recursively
          dest_folder = os.path.join(folder, file)
          if forceoverwrite or overwriteconfig or not os.path.exists(dest_folder):
            shutil.copytree(configfile, folder)
            chown(dest_folder, user, recursive=True)
        elif os.path.isfile(configfile):
          # It is a file... so copy it
          dest_filename = os.path.join(folder, os.path.basename(file))
          if forceoverwrite or overwriteconfig or (not os.path.exists(dest_filename)):
            shutil.copy2(configfile, folder)
            chown(dest_filename, user, recursive=False)
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
    url = 'https://github.com/grycap/osidle',
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

