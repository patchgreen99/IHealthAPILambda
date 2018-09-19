import unittest
import os
from ihealth_metric import retrieveMetricFromIHealthAPI

class TestUM(unittest.TestCase):

    def setUp(self):
        self.credentials = {
            'Client_id': os.environ['TEST_CLIENT_ID'], # The ID for the client request
            'client_secret': os.environ['TEST_CLIENT_SECRET'], # The key for the request
            'access_token': os.environ['TEST_ACCESS_TOKEN'], # The token for access
            'sc': os.environ['TEST_SC'], # The serial number for the user
            'sv': os.environ['TEST_SV'] # This is type of one on one value based on sv
        }

    def test_bg_correct_credentials(self):
        # test that it returns a result
        self.assertTrue('error' not in retrieveMetricFromIHealthAPI('blood_glucose', 9, self.credentials))

    def test_bp_correct_credentials(self):
        # test that it returns a result
        self.assertTrue('error' not in retrieveMetricFromIHealthAPI('blood_pressure', 9, self.credentials))

    def test_bg_correct_datastructure(self):
        # test that it returns the correct datastructure
        (examplekey, examplevalue) = ('20180101', {'unit': None, 'BG': None})

        dataset = retrieveMetricFromIHealthAPI('blood_glucose', 9, self.credentials)
        if dataset:
            (key, value) = dataset.items()[0]
            self.assertEqual(len(key), len(examplekey))
            self.assertEqual(set(value), set(examplevalue))

    def test_bp_correct_datastructure(self):
        # test that it returns the correct datastructure
        (examplekey, examplevalue) = ('20180101', {'unit': None, 'HP': None, 'LP': None})

        dataset = retrieveMetricFromIHealthAPI('blood_pressure', 9, self.credentials)
        if dataset:
            (key, value) = dataset.items()[0]
            self.assertEqual(len(key), len(examplekey))
            self.assertEqual(set(value), set(examplevalue))

if __name__ == '__main__':
    unittest.main()