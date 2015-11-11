from setuptools import setup

def readme():
    with open('README.rst') as f:
        return f.read()

options = {
    'name'              :   'clydepm',
    'description'       :   'Clyde C/C++ Package Manager',
    'long_description'  :   readme(),
    'url'               :   'https://git.crl.vecna.com/#/admin/projects/firmware/tools/python/clydepm',
    'author'            :   'Isaac Gutekunst',
    'author_email'      :   'isaac.gutekunst@vecna.com',
    'license'           :   'Property of Vecna Technologies, Inc.',
    'packages'          :   ['clydepm'],
    'install_requires'  :   ['gitpython', 
                             'pyyaml', 
                             'colorama', 
                             'termcolor', 
                            ],
    'zip_safe'          :   False,
    'version'           :   '0.0.11',
    'test_suite'        :   'nose.collector',
    'tests_require'     :   ['nose'],
    'entry_points'      :   {
        'console_scripts'   :   [ 
            'clyde=clydepm.command_line:main'
        ]
    }
}

setup(**options)
