import sys, os
from subprocess import Popen, PIPE
from termcolor import colored
from clyde2.common import *
import shutil

from clyde2.clyde_logging import get_logger
logger = get_logger()



def makefile_target(rtems_makefile_path, target):
  rtems_makefile_path  = os.path.realpath(rtems_makefile_path)
  with temp_dir() as d:
    with temp_cwd(d):
      with temporary_env({'RTEMS_MAKEFILE_PATH': rtems_makefile_path }):

        # Copy the makefile template into the temporary directory
        template_file = read_template('Makefile-rtems-cflags.mk')
        if not template_file:
          fail("Could not find Makefile-rtems-cflags.mk in templates")

        with open('Makefile', 'w') as makefile:
          makefile.write(template_file)
        
        args = ['make', '-f', 'Makefile']
        args.append(target)
        make = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr = make.communicate()
        logger.debug((colored("Running: " + " ".join(args) + ": ", "yellow")))

        if make.returncode == 0:
          logger.debug(colored('Success', 'green'))
          return stdout.strip()
        else:
          logger.debug(colored("Returned {0}".format(make.returncode), 'red'))
          logger.debug(colored(stderr, 'red'))
          return ""

def get_rtems_cflags(rtems_makefile_path):
  return makefile_target(rtems_makefile_path, 'print-cflags')

def get_rtems_cc(rtems_makefile_path):
  return makefile_target(rtems_makefile_path, 'print-compiler')

def get_rtems_link_flags(rtems_makefile_path):
  full_command = makefile_target(rtems_makefile_path, 'print-link')
  return " ".join(full_command.split()[1:])
      
def get_rtems_link_libs(rtems_makefile_path):
  return makefile_target(rtems_makefile_path, 'print-link-libs')

def get_flags_dict(rtems_makefile_path):
  link_libs = makefile_target(rtems_makefile_path, 'print-link-libs')
  link_flags = makefile_target(rtems_makefile_path, 'print-link')
  cflags = makefile_target(rtems_makefile_path, 'print-cflags')
  cpu_cflags =  makefile_target(rtems_makefile_path, 'print-cpu-cflags')

  link_flags = link_flags.split()
  bsp_specs = link_flags[1] + " -specs bsp_specs -qrtems"
  
  flags = {
    'link_libs'   :    link_libs,
    'cflags'      :       cflags,
    'cpu_cflags'  :   cpu_cflags,
    'bsp_specs'   :   bsp_specs
  }
  return flags



if __name__ == '__main__':
  path = '/home/igutek/rtems/lib-rtems-4.11/arm-rtems4.11/stm32f7x'
  print (get_rtems_cflags())
