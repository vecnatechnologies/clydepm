#!/usr/bin/env python

import argparse
import pkg_resources
import os
from clyde2.package_builder import build_package
from clyde2.generators.generic import generate_file
from clyde2.common import pprint_color

from os.path import join
from termcolor import colored
import traceback

from clydepm.package import Package
from clyde2.clyde_logging import get_logger, init_logging
import logging

def version():
  version = pkg_resources.require("clydepm")[0].version 
  return version

def generate_build_file(path, namespace):
  try:
    options = {}
    if 'variant' in namespace:
      options['variant'] = namespace.variant

    if 'platform' in namespace:
      options['platform'] = namespace.platform
      if options['platform'] == 'rtems':
        if not namespace.rtems:
          rtems_makefile_path = ''
          for rtems_path in ['/arm-rtems4.11', '/arm-rtems4.12']:
            if os.path.exists(rtems_path):
              rtems_makefile_path = join(rtems_path, 'stm32f7x/make/')
          if rtems_makefile_path:
            logging.warn ("Using default RTEMS BSP {0}".format(rtems_makefile_path))
            options['rtems'] = rtems_makefile_path
          else:
            raise Exception("Could not find rtems in / . No BSP specified. Specify with --rtems")

    if 'rtems' in namespace:
      options['rtems'] = namespace.rtems
    
    build_file_contents, tree  = build_package(path, options, fetch_remote = not namespace.fast)
    #build_package(path, options)
    with open(join(path, 'build.ninja'), 'w') as f:
      print(colored("Wrote configuration file build.ninja", 'green'))
      f.write(build_file_contents)
    
    if namespace.verbose:
      pprint_color(tree)
  except Exception as e:
    print (colored(str(e), "red"))
    if (namespace.verbose):
        traceback.print_exc(e)

def main():

  init_logging(logging.DEBUG)
  parser = argparse.ArgumentParser()
  parser.add_argument('--version', action='version', version=version())
  subparsers = parser.add_subparsers(title = 'Commands', dest='command')

  parser_gen = subparsers.add_parser('gen')
  logger = get_logger()


  parser_gen.add_argument('--variant', 
                           type=str, 
                           default = 'src',
                           help = 'Variant to build e.g.  test or linux')

  parser_gen.add_argument("--rtems",
                          type=str,
                          default = None,
                          help = "RTEMS Makefile Path") 

  parser_gen.add_argument("--verbose",
                          action='store_true',
                         default=False,
                         help = "Print a verbose compilation tree")

  parser_gen.add_argument("--fast",
                         action="store_true",
                         default = False,
                         help = "Update dependencies without fetching remote tags ")

  parser_gen.add_argument('--platform', 
                           type=str, 
                           default = 'linux',
                           help = 'platform to build e.g.  linux, rtems')

  commands = {
    'gen'    : generate_build_file,
  }
  
  namespace = parser.parse_args()

  if 'command' in namespace:
    command = namespace.command
    if command in commands:


      path = os.getcwd()
      commands[command](path, namespace)

if __name__ == '__main__':
    main()
