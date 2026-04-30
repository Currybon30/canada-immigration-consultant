import unittest
import os, sys

# Get the parent directory of backend
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

# Import the class
from backend.controllers.agents.cross_check_agent import CrossCheckAgent

class TestCrossCheckAgentTrueModel(unittest.TestCase):
    
    def setUp(self):
        self.agent = CrossCheckAgent()
    
    def test_true_model_with_normal_sentences(self):
        llm_answer = "The capital of France is Paris."
        ref_answer = "Paris is the capital of France."
        score = self.agent.cross_check(llm_answer, ref_answer)
        print("True similarity score (normal sentences):", score)

        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_true_model_with_empty_strings(self):
        score = self.agent.cross_check("", "")
        print("True similarity score (empty strings):", score)

        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_true_model_with_special_characters(self):
        llm_answer = "!!!@@@###"
        ref_answer = "###@@@___"
        score = self.agent.cross_check(llm_answer, ref_answer)
        print("True similarity score (special characters):", score)

        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_true_model_with_unrelated_texts(self):
        llm_answer = "Apples are fruits."
        ref_answer = "The theory of relativity was proposed by Einstein."
        score = self.agent.cross_check(llm_answer, ref_answer)
        print("True similarity score (unrelated texts):", score)

        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_true_model_with_long_paragraphs(self):
        llm_answer = " ".join(["Climate change affects ecosystems."] * 100)
        ref_answer = " ".join(["The environment is impacted by global warming."] * 100)
        score = self.agent.cross_check(llm_answer, ref_answer)
        print("True similarity score (long paragraphs):", score)

        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        
        
    def test_one_sentence_is_none(self):
        llm_answer = "The capital of France is Paris."
        ref_answer = None
        
        with self.assertRaises(TypeError):
            self.agent.cross_check(llm_answer, ref_answer)

if __name__ == '__main__':
    unittest.main()
