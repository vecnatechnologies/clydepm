from clyde2.server import PackageServer, GerritPackageServer, TestServer
from clyde2.package import ClydePackage, TestPackage
from clyde2.resolver import resolve_package_dependencies, create_build_tree
from clyde2.generators.ninja_build import generate_file

from clyde2.common import pprint_color, dict_contains
from clyde2.rtems import get_rtems_cflags, get_rtems_cc

from os.path import join
from os import getenv
import os

def build_package(path, traits = None, generator = None, fetch_remote = True):
  if not generator:
    generator = generate_file

  if 'rtems' in traits and traits['rtems'] and 'CFLAGS' in os.environ:
    raise Exception("CFLAGS and --rtems specified. Please only specify one")

  extra_flags = ''
  if 'rtems' in traits and traits['rtems']:
    print ("Using RTEMS BSP: {0}".format(traits['rtems']))
    #extra_flags = get_rtems_cflags(traits['rtems'])


  elif 'CFLAGS' in os.environ:
    extra_flags = os.environ['CFLAGS']
    # Delete CFLAGS so they don't affect
    # foreign packages
    del os.environ['CFLAGS']
  



  if os.getenv('CC') and len(os.getenv('CC').split()) > 1:
    extra_flags = " ".join(os.getenv('CC').split()[1:]) + ' ' + extra_flags

  traits['cflags']  = ' ' + extra_flags + ' -fdiagnostics-color=always'

  cpp_package = ClydePackage(path, traits)
  server = GerritPackageServer(join(path, 'deps'))


  new_traits = traits.copy()



  if 'variant' in new_traits and new_traits['variant'] == 'test':
    del new_traits['variant']

  if fetch_remote:
    print ("Fetching remotes")
  else:
    print ("Only looking at local git tags")

  packages = resolve_package_dependencies(cpp_package, server, new_traits, fetch_remote)

  packages = {package.name:package for package in packages}
  
  with open(join(path, 'versions.txt'),'w') as f:
    for name, package in packages.iteritems():
      f.write("{0}={1}\n".format(name, package.version))
      package.inflate(packages)

  #cpp_package.inflate(packages)



  tree = create_build_tree(cpp_package)
  rtems_makefile_path = None
  
  if getenv('CC'):
    compiler_prefix = getenv('CC').split()[0].split('gcc')[0]
  elif 'rtems' in traits and traits['rtems']:
    compiler = get_rtems_cc(traits['rtems'])
    rtems_makefile_path = traits['rtems']
    if compiler:
      compiler_prefix = compiler.split()[0].split('gcc')[0]
    else:
      compiler_prefix = ''
  else:
    compiler_prefix = ''
    
  return generator(tree, 
                   prefix = compiler_prefix,
                   root = path,
                   cflags = extra_flags,
                   rtems_makefile_path = rtems_makefile_path)

