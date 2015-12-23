#!/usr/bin/env python
from .package_builder import PackageBuilder
from .package import Package
import argparse
from os.path import realpath, join, exists, expanduser
from os import getcwd
import os
from subprocess import Popen, PIPE
import pkg_resources
import configparser
import getpass

from colorama import init
from termcolor import colored

init()


def load_config(exec_root):
  """
  Load the clyde configuration from several configuration files,
  starting at the most global, and then cascading down to a 
  per project configuration file
  """
# Specify configuration options supported here.
# When load config is called, it looks at all 
# the config dictionary while reading the 
# configuration files, and only looks for 
# options in the config dictionary. This 
# is so malformed dictionaries don't pollute 
# the configuration namespace. 
# This is probably not necessary

  config = {
    'General' : {
      'package-root'    : join(expanduser('~'), '.clyde', 'packages'),
      'git-root'        : join(expanduser('~'), '.clyde', 'git'),
      'user.name'       : getpass.getuser(),
      'user.email'      : None
    }
  
  }

# Configuration for clyde is loaded looking it these configuration
# files in the order specified here. Options specified later will 
# overwrite options specified later
  local_config_path   = join(realpath(exec_root), '.clyde','config')
  user_config_path    = join(expanduser('~'), '.clyde', 'config')
  global_config_path  = '/etc/clyde/config'

  config_paths = [global_config_path,
                  user_config_path,
                  local_config_path]

  for config_path in config_paths:
    if exists(config_path):
      print('Loading {0}'.format(config_path))
      config_parser = configparser.ConfigParser()
      config_parser.readfp(open(config_path))

      for section, options in config.items():
        if config_parser.has_section(section):
          for option, value in options.items():
              if config_parser.has_option(section, option):
                config[section][option] = config_parser.get(section, option)
  return config

def get_gcc_version(compiler_binary):
  """
  Runs gcc and extracts the version string
  """
  args = [compiler_binary, '-dumpversion']
  gcc = Popen(args, stdout=PIPE, stderr=PIPE)
  stdout, stderr = gcc.communicate()
  return stdout.split()[0]


def make_package_descriptor(path, variant = None):
  """
  Make a valid package descriptor for the clyde package located
  at path.

  This cares about the environment variables
  CC      : Use this compiler
  CFLAGS  : Pass these extra CFLAGS to the compiler (and all dependencies)
  """
  if 'CC' in os.environ:
    cc = os.getenv('CC').split()[0]
  else:
    cc = 'gcc'

  compiler_version = get_gcc_version(cc)


  temp_package = Package(path, form = 'source')
  traits = { 
      'compiler'          : cc,
      'compiler-version'  : compiler_version
    
    }

  config = temp_package.get_configuration()


  if 'CFLAGS' in os.environ:
    extra_flags = os.environ['CFLAGS']
    # Delete CFLAGS so they don't affect
    # foreign packages
    del os.environ['CFLAGS']
  else:
    extra_flags = ''

  if os.getenv('CC') and len(os.getenv('CC').split()) > 1:
    extra_flags = " ".join(os.getenv('CC').split()[1:]) + ' ' + extra_flags

  traits['cflags'] = ' ' + extra_flags
  
  if variant:
    traits['variant'] = variant

  
  descriptor = {
    'name'        : config['name'],
    'version'     : 'local',
    'local-path'  : path,
    'form'        : 'source',
    'traits'      : traits
  }
  return descriptor


def is_package(path):

  path = realpath(path)
  return exists(join(path, 'config.yaml')) or exists(join(path, 'descriptor.yaml'))



def make(builder, variant = 'src'):
  project_root = getcwd()
  if not is_package(project_root):
    raise Exception("This isn't a package {0}".format(project_root))
  descriptor = make_package_descriptor(project_root, variant)

  return builder.get_package_by_descriptor(descriptor)


def clean(builder):
  package = make(builder).clean()
  print ('cleaning')
  pass


def run_binary(binary):
  if os.path.exists(binary):
    args = [binary]
    test_binary = Popen(args, stdout=PIPE, stderr=PIPE)
    stdout, stderr = test_binary.communicate()
    print("Running test executable")
    print (stdout)
    print((colored(stderr, 'red')))
  else:
    print((colored('Failed to run. Test executable is missing.', 'red')))

def run(builder):
  package = make(builder)
  binary = package.get_binary()
  run_binary(binary)


def test(builder):
  print('Testing')
  package = make(builder, variant = 'test')
  binary = package.get_binary()
  run_binary(binary)

def init(builder, package_type = 'application'):
  print('initializing')
  builder.create_new_package(os.getcwd(), package_type)
  pass

def config(builder):
  print('configuring')
  pass

def version():
  version = pkg_resources.require("clydepm")[0].version 
  return version


def main():



  parser = argparse.ArgumentParser()
  parser.add_argument('--version', action='version', version=version())
  subparsers = parser.add_subparsers(title = 'Commands', dest='command')

  parser_make     = subparsers.add_parser('build')
  parser_init     = subparsers.add_parser('init')
  parser_clean    = subparsers.add_parser('clean')
  parser_test     = subparsers.add_parser('test')
  parser_run      = subparsers.add_parser('run')

  parser_init.add_argument('type', type=str, help = 'Type of package (application or library')

  commands = {
    'build'    : make,
    'clean'   : clean,
    'test'    : test,
    'config'  : config,
    'init'    : init,
    'run'     : run,
  }
  
  namespace = parser.parse_args()

  if 'command' in namespace:
    command = namespace.command
    if command in commands:
      options = {}

      configuration = load_config(getcwd())
      package_builder = PackageBuilder(configuration)

      if 'type' in namespace:
        commands[command](package_builder, namespace.type)
      else:
        commands[command](package_builder)



if __name__ == '__main__':
    main()
