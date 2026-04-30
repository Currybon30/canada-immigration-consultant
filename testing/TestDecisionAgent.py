import unittest
import sys
import os
# Get the parent directory of backend
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Add it to sys.path
sys.path.append(parent_dir)

from backend.controllers.agents.decision_agent import DecisionAgent

class TestDecisionAgent(unittest.TestCase):

    def setUp(self):
        path = os.path.join(parent_dir, 'backend')

        self.agent = DecisionAgent(path)

    def test_classify_question_visa(self):
        question = "What are the visa application requirements?"
        self.assertEqual(self.agent.classify_question(question), "visa")

    def test_classify_question_study_permit(self):
        question = "How do I apply for a study permit to a college?"
        self.assertEqual(self.agent.classify_question(question), "study permit")

    def test_classify_question_pgwp(self):
        question = "What is the eligibility for a post-graduate work permit?"
        self.assertEqual(self.agent.classify_question(question), "pgwp")

    def test_classify_question_crs(self):
        question = "How many points do I need for express entry invitation?"
        self.assertEqual(self.agent.classify_question(question), "crs")
        
    def test_classify_question_empty_string(self):
        question = ""
        with self.assertRaises(ValueError):
            print(self.agent.classify_question(question))


if __name__ == '__main__':
    unittest.main(exit=False)