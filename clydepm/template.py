from jinja2 import Template
import yaml
from pkg_resources import resource_filename
from os.path import join, realpath, exists, relpath
from os import getcwd, makedirs
import sys
import datetime

def fail(str):
  sys.stderr.write(str + '\n')
  sys.exit(1)

def extract(d):
  key = list(d.keys())[0]
  values = d[key]
  return key, values

def resource(name):
  filename = resource_filename(__name__, join('../', name))
  return filename

def fetch(name = None, config = None, descriptor = None):
  template = find_template_by_name(name)
  if template:
    expand_template(template, config, descriptor)
  else:
    fail ("Template {0} does not exist\n".format(name))


def find_template_by_name(name):
  filename = resource('template_config.yaml')
  with open(filename) as f:
    config = yaml.load(f)
    template_document = config['templates']
    for template in template_document:
      key, values = extract(template)
      if name == key:
        return values
  return None

def template_resource(template):
  return realpath(resource(join('templates', template)))


def get_template_tuple(file_entry):
  if type(file_entry) == str:
    filename = template_resource(file_entry)
    target_filename = file_entry
  elif type(file_entry) == dict:
    filename, values = extract(file_entry)
    filename = template_resource(filename)
    if 'as' in values:
      target_filename = values['as']
  else:
    filename, target_filename = None, None

  return (filename, target_filename)


def expand_template(template_entry, config, descriptor):
  if not 'include' in template_entry:
    fail("Each template_entry entry must have an include entry")
  includes = template_entry['include']

  if not 'directory' in template_entry:
    fail("Each template_entry entry must have a directory entry")

  dir = realpath(join(getcwd(), template_entry['directory']))
  if not exists(dir):
    makedirs(dir)
  for file_entry in includes:
    source, target_filename = get_template_tuple(file_entry)
    target_filename = relpath(join(dir, target_filename))
    if not exists(source):
      fail("Clyde Error: template_entry source file {0} does not exist".format(filename))

    if exists(target_filename):
      print("Error: target template_entry file {0} exists Refusing to overwrite".format(target_filename))

    args = {'date'      : datetime.datetime.now() ,
            'year'      : datetime.datetime.now().strftime("%Y"),
            'version'   : descriptor['version'],
            'revision'  : descriptor['version'],
            'name'      : descriptor['name'],
            'Name'      : descriptor['name'].capitalize(),
            'user.name' : config['user.name'],
            'user.email': config['user.email']
           }
    with open(source) as source_template_entry:
      t = Template(source_template_entry.read())
      with open(target_filename, 'w') as target:
        target.write(t.render(**args))
        print ("Created {0}".format(target_filename))




