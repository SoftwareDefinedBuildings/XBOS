import unittest
import pandas as pd

import sys
sys.path.append("..")
from Energy_Analytics import Wrapper

class TestImport(unittest.TestCase):

    # @classmethod
    # def setUpClass(cls):
    #     main_obj = Wrapper()

    # @classmethod
    # def tearDownClass(cls):
    #   pass

    def setUp(self):
      self.main_obj = Wrapper()

    # def tearDown(self):
    #   pass

    def test_import_csv(self):
        
        # Incorrect head_row
        with self.assertRaises(Exception) as context:
            self.main_obj.import_data(folder_name='../data/', head_row=[-1,5,0])
        
        # Incorrect head_row
        with self.assertRaises(Exception) as context:         
            self.main_obj.import_data(folder_name='../data/', head_row=[-1,5,0,1,2,3])

        # Incorrect folder name
        with self.assertRaises(NotImplementedError) as context:
            self.main_obj.import_data(file_name='blah.csv', folder_name=['blah', 'blah'])

        # Can't have file_name and folder_name both of type list
        with self.assertRaises(NotImplementedError) as context:
            self.main_obj.import_data(file_name=['blah1.csv', 'blah2.csv'], folder_name=['blah1', 'blah2'])

        # Incorrect file extension
        with self.assertRaises(Exception) as context:
            self.main_obj.import_data(file_name='blah.txt', folder_name='../')

        # Can't have multiple folders
        with self.assertRaises(NotImplementedError) as context:
            self.main_obj.import_data(folder_name=['one', 'two'])


if __name__ == '__main__':
    unittest.main()