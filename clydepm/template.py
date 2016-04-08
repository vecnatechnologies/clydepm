from jinja2 import Template
import yaml
from os.path import join, realpath, exists, relpath
from os import getcwd, makedirs
import sys
import datetime
from termcolor import colored

from clyde2.common import *
from clyde2.clyde_logging import get_logger
logger = get_logger()



def extract(d):
  key = list(d.keys())[0]
  values = d[key]
  return key, values


def fetch(name = None, config = None, descriptor = None, list = False):
  if list:
    print ("Available templates\n")
  template = find_template_by_name(name, list)
  if template:
    expand_template(template, config, descriptor)
  elif list:
    return
  else:
    fail ("Template {0} does not exist\n".format(name))


def find_template_by_name(name, list):
  filename = resource('template_config.yaml')
  config = read_template('template_config.yaml')
  config = yaml.load(config)
  template_document = config['templates']

  # Get the largest width key for nice formatting
  col_width = max(map(lambda a: len(a[0]), map(extract, template_document)))
  for template in template_document:
    key, values = extract(template)
    if list:
      if 'description' in values:
        print ("{0} - {1}".format(key.ljust(col_width), values['description']))
      else:
        print ("{0}".format(key))

    if name == key:
      return values
  return None



def get_template_tuple(file_entry):
  if type(file_entry) == str:
    target_filename = file_entry
    filename = file_entry
  elif type(file_entry) == dict:
    filename, values = extract(file_entry)
    if 'as' in values:
      target_filename = values['as']
    else:
      print ("values", values)
      fail("malformed  include configuration")
  else:
    filename, target_filename = None, None

  return (filename, target_filename)


def expand_template(template_entry, config, descriptor):
  if 'meta-include' in template_entry:
    for entry in template_entry['meta-include']:
      fetch(entry, config, descriptor)
    return

  if not 'include' in template_entry:
    fail("Each template_entry entry must have an include entry")
  includes = template_entry['include']

  if not 'directory' in template_entry:
    fail("Each template_entry entry must have a directory entry")

  dir =template_entry['directory']
  vars = {'$PWD' : lambda d: getcwd()}
  if dir in vars:
    dir = vars[dir](dir)
  else:
    dir = realpath(join(getcwd(), dir))

  if not exists(dir):
    makedirs(dir)

  for file_entry in includes:
    source, target_filename = get_template_tuple(file_entry)
    target_filename = relpath(join(dir, target_filename))

    template_contents = read_template(source)
    if not template_contents:
      fail("template_entry source file {0} does not exist".format(source))

    if exists(target_filename):
      warn("Refusing to overwrite existing file {0}".format(target_filename))
      continue

    args = {'date'      : datetime.datetime.now() ,
            'year'      : datetime.datetime.now().strftime("%Y"),
            'version'   : descriptor['version'],
            'revision'  : descriptor['version'],
            'name'      : descriptor['name'],
            'Name'      : descriptor['name'].capitalize(),
            'user.name' : config['user.name'],
            'user.email': config['user.email']
           }
    
    t = Template(template_contents)
    with open(target_filename, 'w') as target:
      target.write(t.render(**args))
      print ("Created {0}".format(target_filename))

    if 'message' in template_entry:
      message = template_entry['message']
      print (colored(message, "green"))




