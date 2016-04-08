import os, getpass
import json
import git

from pygerrit.client import GerritClient
from semantic_version import Version, Spec
from termcolor import colored
from subprocess import Popen, PIPE

from .common import stable_sha, temp_cwd
from .package import ClydePackage

class PackageServer(object):

  def search(self, name, version_string = None):
    return []



class GerritPackageServer(object):

  def __init__(self, git_directory = "/home/igutek/clyde2/git"):
    self.git_directory = git_directory
    if not os.path.exists(self.git_directory):
      os.makedirs(self.git_directory)
    self.tags = {}


  def lsremote(self, url):
    remote_refs = {}
    g = git.cmd.Git()
    for ref in g.ls_remote(url).split('\n'):
      hash_ref_list = ref.split('\t')
      remote_refs[hash_ref_list[1]] = hash_ref_list[0]
    return remote_refs

  def lslocal(self, name, fetch_remote):
    path = os.path.join(self.git_directory, name)
    if os.path.exists(path):
      repo = git.Repo(path)
      origin = repo.remotes.origin
      if fetch_remote:
        origin.fetch()
      tags = [Version(str(tag)) for tag in repo.tags]
      return tags

  def list_tags(self, name, fetch_remote):
    if name in self.tags:
      return self.tags[name]
    def istag(str):
      return str.startswith("refs/tags") and not str.endswith("^{}")

    path = "gerrit:/clyde/packages/"  + name
    if not os.path.exists(os.path.join(self.git_directory, name)):
      if not self.checkout_remote_repo(path):
        raise Exception("Could not find project {0} locally or on gerrit".format(name))
    
    #print (colored(self.lslocal(name), "red"))
    #versions = [Version(s[10:], partial=True) for s in filter(istag, self.lsremote(path))]
    self.tags[name] = self.lslocal(name, fetch_remote)
    return self.tags[name]


  def search_projects(self, name):
    client = GerritClient("gerrit")

    results = client.run_command("ls-projects --format json")
    projects = json.load(results.stdout)

    clyde_projects = []
    for name, contents in projects.iteritems():
      if name.startswith('clyde/packages'):
          clyde_projects.append(name.split('/')[2])

    return clyde_projects


  def search(self, name, spec = None, fetch_remote = True):
    if spec:
      return spec.filter(self.list_tags(name, fetch_remote))
    else:
      return self.list_tags(name, fetch_remote)


  def best(self, name, spec, traits = None, fetch_remote = True):
    if not spec:
      raise Exception("Need a spec")
    tags = self.list_tags(name, fetch_remote)
    options = list(spec.filter(tags))
    best_version =  spec.select(options)

    return self.get_project(name, best_version, traits, fetch_remote)


  def get_project(self, name, version, traits, remote_fetch):
    dir = os.path.join(self.git_directory, name)
    if not os.path.exists(dir):
      self.checkout_remote_project(name)
    if not version:
      return None
    g = git.Git(dir)
    repo = git.Repo(dir)
    if remote_fetch:
      repo.remotes.origin.fetch()

    g.checkout(version)
    return ClydePackage(dir, traits)


  def checkout_remote_repo(self, repo_path):
    name = os.path.split(repo_path)[1]
    with temp_cwd(self.git_directory):
      args = ['git','clone', repo_path]
      git = Popen(args, stdout=PIPE, stderr=PIPE)
      stdout, stderr = git.communicate()
      if git.returncode == 0:
        return True
      return False


  def checkout_remote_project(self, project_name):
    username = username = getpass.getuser()
    if username == 'igutek':
        username = "isaac.gutekunst"
    base_url = 'ssh://{0}@git.crl.vecna.com:29418/clyde/packages/{1}'.format(username,
                                                                  project_name)
    print((colored('Checking out {0}'.format(base_url),'green')))
    return self.checkout_remote_repo(base_url)



class TestServer(object):

  def __init__(self):
    self.packages = {}


  def add_package(self, package):
    if package.name in self.packages:
      self.packages[package.name][package.version] = package
    else:
      self.packages[package.name] = {package.version: package}

  def search(self, name, spec = None):
    if name not in self.packages:
      return []

    versions = [p for p in self.packages[name].keys()]  
    if spec:
      versions = spec.filter(versions)

    results = [self.packages[name][v] for v in versions]
    return results


  def best(self, name, spec):
    if not spec:
      raise Exception("Need a spec")

    if name not in self.packages:
      return None

    versions = [p for p in self.packages[name].keys()]  

    version = spec.select(versions)
    if version:
      return self.packages[name][version]
    else:
      return None


class LocalGitServer(object):

  def __init__(self, git_directory = "/home/igutek/clyde2/git"):
    self.git_directory = git_directory
    if not os.path.exists(self.git_directory):
      os.makedirs(self.git_directory)
  


  def list_tags(self, name):
    dir = os.path.join(self.git_directory, name)
        
    if not os.path.exists(dir):
      return []

    repo = git.Repo(dir)
    
    
    versions = [Version(s[10:], partial=True) for s in filter()]
    return versions


  def search_projects(self, name):
    client = GerritClient("gerrit")

    results = client.run_command("ls-projects --format json")
    projects = json.load(results.stdout)

    clyde_projects = []
    for name, contents in projects.iteritems():
      if name.startswith('clyde/packages'):
          clyde_projects.append(name.split('/')[2])

    return clyde_projects


  def search(self, name, spec = None):
    if spec:
      return spec.filter(self.list_tags(name))
    else:
      return self.list_tags(name)


  def best(self, name, spec):
    if not spec:
      raise Exception("Need a spec")
    options = self.list_tags(name)
    best_version =  spec.select(options)
    return self.get_project(name, best_version)


  def get_project(self, name, version):
    dir = os.path.join(self.git_directory, name)
    if not os.path.exists(dir):
      self.checkout_remote_project(name)

    return ClydePackage(dir)


  def checkout_remote_repo(self, repo_path):
    name = os.path.split(repo_path)[1]
    with temp_cwd(self.git_directory):
      args = ['git','clone', repo_path]
      git = Popen(args, stdout=PIPE, stderr=PIPE)
      stdout, stderr = git.communicate()
      if git.returncode == 0:
        return True
      return False


  def checkout_remote_project(self, project_name):
    username = username = getpass.getuser()
    if username == 'igutek':
        username = "isaac.gutekunst"
    base_url = 'ssh://{0}@git.crl.vecna.com:29418/clyde/packages/{1}'.format(username,
                                                                  project_name)
    print((colored('Checking out {0}'.format(base_url),'green')))
    return self.checkout_remote_repo(base_url)

