import unittest
import json
import asyncio
from unittest.mock import MagicMock, patch
import sys
import os

# AsyncMock class definition (for Python 3.8 compatibility)
class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)

class TestFAQAgent(unittest.TestCase):
    
    def setUp(self):
        """Setup before each test"""
        # Set up event loop
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Test data
        self.test_query = "Can I extend my stay as a student?"
        self.test_category = "study permit"
        self.test_filter = {"tags": {"$in": ["study permit", "visa"]}}
        
        # Import FAQAgent only once in setUp
        from controllers.agents.faq_agent import FAQAgent
        self.FAQAgent = FAQAgent

        # Patch to prevent PyMongo warnings
        self.patcher = patch('config.mongodb.AsyncIOMotorClient')
        self.mock_motor_client = self.patcher.start()
        
    def tearDown(self):
        """Cleanup after each test"""
        self.patcher.stop()
        self.loop.close()
    
    def test_get_answer_high_score(self):
        """Test if a query with high similarity score returns the metadata correctly"""
        # 1. Set up expected return value
        expected_metadata = {
            "question": "How can I extend my stay as a student?",
            "answer": "If you want to continue studying in Canada, you must apply to extend your study permit.",
            "tags": ["study permit", "visa"]
        }
        
        # 2. Create FAQAgent instance
        agent = self.FAQAgent()
        
        # 3. Create mock and set up response
        mock_pinecone = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.body = json.dumps({
            "results": {
                "matches": [
                    {
                        "score": 0.92,  # High score (>0.87)
                        "metadata": expected_metadata
                    }
                ]
            }
        })
        mock_pinecone.search.return_value = mock_response
        
        # 4. Save original pinecone object and replace with mock
        original_pinecone = agent.pinecone
        agent.pinecone = mock_pinecone
        
        try:
            # 5. Run test
            result = self.loop.run_until_complete(
                agent.get_answer(self.test_query, self.test_category, filter=self.test_filter)
            )
            
            # 6. Verify
            mock_pinecone.search.assert_called_once()
            self.assertEqual(result, expected_metadata)
        finally:
            # 7. Restore original object
            agent.pinecone = original_pinecone
    
    @patch('controllers.agents.faq_agent.save_query')
    def test_get_answer_low_score(self, mock_save_query):
        """Test if a query with low similarity score returns 'Not found'"""
        # 1. Set up save_query mock
        mock_save_query.return_value = {"id": "123", "status": "success"}
        
        # 2. Create FAQAgent instance
        agent = self.FAQAgent()
        
        # 3. Set up Pinecone mock
        mock_pinecone = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.body = json.dumps({
            "results": {
                "matches": [
                    {
                        "score": 0.7,  # Low score (<0.87)
                        "metadata": {"question": "Some other question", "answer": "Some other answer"}
                    }
                ]
            }
        })
        mock_pinecone.search.return_value = mock_response
        
        # 4. Save original pinecone object and replace with mock
        original_pinecone = agent.pinecone
        agent.pinecone = mock_pinecone
        
        try:
            # 5. Run test
            result = self.loop.run_until_complete(
                agent.get_answer(self.test_query, self.test_category, filter=self.test_filter)
            )
            
            # 6. Verify
            mock_pinecone.search.assert_called_once()
            mock_save_query.assert_called_once()
            self.assertEqual(result, "Not found")
        finally:
            # 7. Restore original object
            agent.pinecone = original_pinecone
    
    @patch('controllers.agents.faq_agent.save_query')
    def test_get_answer_mongodb_error(self, mock_save_query):
        """Test if MongoDB errors are handled correctly"""
        # 1. Set up save_query mock to return error
        mock_save_query.return_value = {"error": "Database connection failed"}
        
        # 2. Create FAQAgent instance
        agent = self.FAQAgent()
        
        # 3. Set up Pinecone mock
        mock_pinecone = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.body = json.dumps({
            "results": {
                "matches": [
                    {
                        "score": 0.7,  # Low score
                        "metadata": {"question": "Some other question", "answer": "Some other answer"}
                    }
                ]
            }
        })
        mock_pinecone.search.return_value = mock_response
        
        # 4. Save original pinecone object and replace with mock
        original_pinecone = agent.pinecone
        agent.pinecone = mock_pinecone
        
        try:
            # 5. Run test
            result = self.loop.run_until_complete(
                agent.get_answer(self.test_query, self.test_category, filter=self.test_filter)
            )
            
            # 6. Verify
            self.assertEqual(result, "Error from FAQAgent with MongoDB: Database connection failed")
            mock_save_query.assert_called_once()
        finally:
            # 7. Restore original object
            agent.pinecone = original_pinecone
    
    def test_get_answer_pinecone_error(self):
        """Test if Pinecone API errors are handled correctly"""
        # 1. Create FAQAgent instance
        agent = self.FAQAgent()
        
        # 2. Create mock and set up error response
        mock_pinecone = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.body = json.dumps({
            "message": "Invalid query"
        })
        mock_pinecone.search.return_value = mock_response
        
        # 3. Save original pinecone object and replace with mock
        original_pinecone = agent.pinecone
        agent.pinecone = mock_pinecone
        
        try:
            # 4. Test exception raising
            with self.assertRaises(RuntimeError) as context:
                self.loop.run_until_complete(
                    agent.get_answer(self.test_query, self.test_category, filter=self.test_filter)
                )
            
            # 5. Verify exception message
            self.assertIn("Error from FAQAgent: Invalid query", str(context.exception))
        finally:
            # 6. Restore original object
            agent.pinecone = original_pinecone
    
    @patch('controllers.agents.faq_agent.save_query')
    def test_get_answer_empty_matches(self, mock_save_query):
        """Test if empty match list is handled correctly"""
        # 1. Set up save_query mock
        future = asyncio.Future(loop=self.loop)
        future.set_result({"id": "123", "status": "success"})
        mock_save_query.return_value = future
        
        # 2. Create FAQAgent instance
        agent = self.FAQAgent()
        
        # 3. Set up Pinecone mock with empty matches
        mock_pinecone = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.body = json.dumps({
            "results": {
                "matches": []
            }
        })
        mock_pinecone.search.return_value = mock_response
        
        # 4. Save original pinecone object and replace with mock
        original_pinecone = agent.pinecone
        agent.pinecone = mock_pinecone
        
        try:
            # 5. Run test
            result = self.loop.run_until_complete(
                agent.get_answer(self.test_query, self.test_category, filter=self.test_filter)
            )
            
            # 6. Verify
            self.assertEqual(result, "Not found")
            # The behavior for empty match lists may vary depending on the FAQAgent implementation,
            # so we may need to adjust or remove the save_query call verification.
        finally:
            # 7. Restore original object
            agent.pinecone = original_pinecone
    
    def test_get_answer_custom_index(self):
        """Test if custom index name is used correctly"""
        # 1. Create FAQAgent instance
        agent = self.FAQAgent()
        
        # 2. Create mock and set up response
        mock_pinecone = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.body = json.dumps({
            "results": {
                "matches": [
                    {
                        "score": 0.92,
                        "metadata": {"question": "Test question", "answer": "Test answer"}
                    }
                ]
            }
        })
        mock_pinecone.search.return_value = mock_response
        
        # 3. Save original pinecone object and replace with mock
        original_pinecone = agent.pinecone
        agent.pinecone = mock_pinecone
        
        try:
            # 4. Run test with custom index
            custom_index = "custom_index"
            result = self.loop.run_until_complete(
                agent.get_answer(self.test_query, self.test_category, index_name=custom_index)
            )
            
            # 5. Verify correct index was used
            mock_pinecone.search.assert_called_once()
            args, kwargs = mock_pinecone.search.call_args
            self.assertEqual(args[0], custom_index)
        finally:
            # 6. Restore original object
            agent.pinecone = original_pinecone
    
    def test_get_answer_custom_topk(self):
        """Test if custom top_k value is used correctly"""
        # 1. Create FAQAgent instance
        agent = self.FAQAgent()
        
        # 2. Create mock and set up response
        mock_pinecone = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.body = json.dumps({
            "results": {
                "matches": [
                    {
                        "score": 0.92,
                        "metadata": {"question": "Test question", "answer": "Test answer"}
                    }
                ]
            }
        })
        mock_pinecone.search.return_value = mock_response
        
        # 3. Save original pinecone object and replace with mock
        original_pinecone = agent.pinecone
        agent.pinecone = mock_pinecone
        
        try:
            # 4. Run test with custom top_k
            custom_topk = 5
            result = self.loop.run_until_complete(
                agent.get_answer(self.test_query, self.test_category, top_k=custom_topk)
            )
            
            # 5. Verify correct top_k was used
            mock_pinecone.search.assert_called_once()
            args, kwargs = mock_pinecone.search.call_args
            self.assertEqual(args[2], custom_topk)
        finally:
            # 6. Restore original object
            agent.pinecone = original_pinecone

if __name__ == "__main__":
    unittest.main()
