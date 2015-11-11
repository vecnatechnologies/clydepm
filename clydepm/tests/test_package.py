import unittest
import os
from os.path import join
import shutil
from common import temp_cwd

class ClydePackageTester(unittest.TestCase):

  def setUp(self):

    self.test_dir = join(os.getcwd(), 'clyde-test-packages')

    if os.path.exists(self.test_dir):
      raise Exception("Test directory {0} should not exist".format(self.test_dir))
    os.makedirs(self.test_dir)

  def tearDown(self):
    if not os.path.exists(self.test_dir):
      raise Exception("Test directory {0} should exist".format(self.test_dir))
    shutil.rmtree(self.test_dir)



class TestTrivialApplication(ClydePackageTester):

  def test_init_application(self):
    test_app_dir = join(self.test_dir, 'test-application')
    os.makedirs(test_app_dir)
    with temp_cwd(test_app_dir):
      pass
      


    pass
