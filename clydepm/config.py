import pkg_resources
import configparser
import getpass
from os.path import realpath, join, exists, expanduser

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
