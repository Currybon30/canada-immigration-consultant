import unittest
import os
import sys

# Get the parent directory of backend
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Add it to sys.path
sys.path.append(parent_dir)

from backend.controllers.agents.crs_links_agent import CRSLinksAgent

class TestCRSLinksAgent(unittest.TestCase):

    def setUp(self):
        self.agent = CRSLinksAgent()

    def test_get_recommendations_link_match(self):
        user_input = "How to calculate CRS score points?"
        expected_recommendation = {'CRS Calculator': 'https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/express-entry/check-score.html'}
        self.assertDictEqual(self.agent.get_recommendations(user_input), expected_recommendation)

    def test_get_recommendations_no_link_match(self):
        user_input = "What time is it?"
        expected_recommendation = 'No recommendations found'
        self.assertEqual(self.agent.get_recommendations(user_input), expected_recommendation)
        
    def test_get_recommendations_empty_string(self):
        user_input = ""
        
        with self.assertRaises(ValueError):
            print(self.agent.get_recommendations(user_input))
        
if __name__ == '__main__':
    unittest.main(exit=False)