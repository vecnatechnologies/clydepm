from .package import Package
import os
import hashlib
import shutil
import yaml
from os.path import splitext, join, realpath
from .common import stable_sha
from .git_package_server import LocalGitPackageServer, LocalForeignPackagerServer
import tarfile
from distutils.dir_util import copy_tree
import pprint

pp = pprint.PrettyPrinter(indent=4)


class PackageBuilder(object):
  """
  A package server maintains a database that stores packages in 
  various forms. Currently supported forms are binary and source.
  
  Package versions are specified as GIT_RESPEC, with a few keywords
  reserved for special purposes. In future versions of this server,
  the versioning system may include other methods for retrieving packages
  that don't actually use the version as  GIT_REFSPEC directly.
  
  Right now, local is a reserved version name used to indicate 
  a package should be retrieved from a locally accessible directory
  rather than specifying a specific version.

  In addition, packages have various traits (usually only for binary forms),
  that represent how the package was actually built.


  To support caching and remote repositories, a package server can
  have references to upstream PackageServers, so that if a package
  cannot be retrieved locally, it can be retrieved remotely.

  For binary packages, the search order is as follows:

    Local cache
    Remote cache
    Local source cache and build
    Remote source cache retrieve, and build from local cache

  For source packages, the search is:
    Local source cache Remote source cache

  Note, there really isn't a difference from cache and source cache.

  The only difference is form of the requested package


  """
  def __init__(self, configuration):
    package_root = configuration['General']['package-root']
    git_root     = configuration['General']['git-root']

    self.configuration = configuration

    if package_root is None:
      self.root_directory = realpath(os.getcwd())
    else:
      self.root_directory = realpath(package_root)

    if git_root is None:
      self.local_git = LocalGitPackageServer(join(self.root_directory, 'git-server'))
    else:
      self.local_git = LocalGitPackageServer(git_root)


    self.package_servers = [self.local_git]

    self.package_directory = join(self.root_directory, '.packages')

  def store_tarball(self, tarball_path):
    """
    Extract and store a tarball in local cache
    """

    if tarball_path.endswith('.tar.gz'):
      sha = os.path.split(tarball_path.replace('.tar.gz', ''))[1]
      path = join(self.package_directory, sha) 
      with tarfile.open(tarball_path) as tar:
        tar.extractall(self.package_directory)
    else:
      raise Exception("store_tarball not passed .tar.gz file")
    
  def create_new_package(self, new_package_directory, package_type):

    Package.create_new_package(new_package_directory, 
                               package_type,
                               self.configuration)
  
  def store_package(self, package, descriptor):
    path  = join(self.package_directory, stable_sha(descriptor))

    if os.path.exists(path):
      print ("Overwriting existing package!")

    # Copy from archive_dir to path
    #print "Copying {0} -> {1}".format(package.get_archive_dir(), path)
    copy_tree(package.get_archive_dir(), path)



  def get_package_by_descriptor(self, descriptor):
    """
    Given a python dictionary describing a package, retrieve 
    it using whatever techniques are necessary.

    This may require building the package, and recursively 
    retrieving all the dependencies

    """
    hash = stable_sha(descriptor)
    # packages are stored in root/.packages/


    package_paths = [d for d in os.listdir(self.package_directory)]
    name = descriptor['name']

    if descriptor['version'] == 'local':
      pass

    elif hash not in package_paths:
      hash = stable_sha(descriptor)  
      if hash not in package_paths:
        for server in self.package_servers:
          package_tarball_path = server.get_package_tarball_by_descriptor(descriptor)
          if package_tarball_path:
              self.store_tarball(package_tarball_path)
              break
        if package_tarball_path is None:
          for server in self.package_servers:
            descriptor['form'] = 'source'
            package_tarball_path = server.get_package_tarball_by_descriptor(descriptor)
            if package_tarball_path:
                self.store_tarball(package_tarball_path)
                break
          if package_tarball_path is None:
            raise Exception("Failed to find package {0} anywhere".format(name))
      else:
        print(("Found {0} sources locally".format(name + '-' +
                                                 descriptor['version'])))

    else:
      pass

    # If the binary package didn't exist, the descriptor might be changed.
    # Rebuild the sha

    if descriptor['version'] == 'local':
      package_path = descriptor['local-path']
      descriptor['form'] = 'source'
    else:
      hash = stable_sha(descriptor)  
      package_path = join(self.package_directory, hash)

    package = Package(package_path, descriptor['form'], descriptor['traits'])



    if package:
      form = descriptor['form']
        
      if form == 'source':
        # Make a copy of the parent descriptor
        parent_descriptor = descriptor.copy()
        dependencies = self.get_package_dependencies(package, parent_descriptor) 
        for d in dependencies:
          d.copy_artifacts(package.get_dependency_dir())
        
        print(("Building {0}-{1}".format(package.config['name'],
                                       package.config['version'])))
        package.build()
        descriptor['form'] = package.get_form()
        package.create_archive(descriptor)
        self.store_package(package, descriptor)
      elif form =='binary':
        print(("Package {0}-{1} already built".format(descriptor['name'],
                                                      descriptor['version'])))



      return package
         
    else:
      print ("Failed to retrieve package")

  def get_package_dependencies(self, package, parent_descriptor):
    """
    Look through dependencies, and construct package 
    description needed to retrieve each package. Then go ahead
    and get those packages, potentially causing some more recursion
    
    """
    packages = []
    parent_descriptor['requires'] = package.get_dependency_configurations()
    for dep_name, dep_config in package.get_dependency_configurations().items():
      
      descriptor = self.make_package_descriptor(package, parent_descriptor,
                                                dep_name)
      package = self.get_package_by_descriptor(descriptor)
      packages.append(package)
    return packages

  def make_package_descriptor(self, package, parent_descriptor, dep_name):

    traits = package.get_traits()
    if 'variant' in traits:
        del traits['variant']
    descriptor = {
      'name'          : dep_name,
      'version'       : parent_descriptor['requires'][dep_name]['version'],
      'form'          : 'binary',
      'traits'        : traits
    }

    if descriptor['version'] == 'local':
      local_path = parent_descriptor['requires'][dep_name]['local-path']
      #local_path = realpath(join(package.get_path(), local_path))
      descriptor['local-path'] = local_path
    descriptor['traits']['cflags'] = parent_descriptor['traits']['cflags']
    print("pt", parent_descriptor)
    # Copy all the elements from the dep_config
    # into the descriptor (name, version, local-path, base-version)
    return descriptor




  def build_package_by_description(self, descriptor):
    pass


  def build_package(self, package):
    pass


