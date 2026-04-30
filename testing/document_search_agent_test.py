import pytest
import json
from backend.controllers.agents.document_search_agent import DocumentSearchAgent


@pytest.fixture
def agent():
    return DocumentSearchAgent()


def mock_response(status_code, body):
    class MockResponse:
        def __init__(self, status_code, body):
            self.status_code = status_code
            self.body = json.dumps(body)
    
    return MockResponse(status_code, body)


# Test 1: Test successful document search
def test_find_documents_success(agent):
    mock_docs = mock_response(200, {
        "results": {
            "matches": [
                {"score": 0.80, "metadata": {"text": "Apply for a study permit"}},
                {"score": 0.75, "metadata": {"text": "Eligibility criteria for study permit"}}
            ]
        }
    })
    
    agent.pinecone.search = lambda *args, **kwargs: mock_docs
    result = agent.find_documents("How do I apply for a study permit?")
    
    assert result.status_code == 200


# Test 2: Test failure during document search
def test_find_documents_failure(agent):
    mock_docs = mock_response(500, {"message": "Internal server error"})
    agent.pinecone.search = lambda *args, **kwargs: mock_docs
    
    with pytest.raises(RuntimeError, match="Internal server error"):
        agent.find_documents("How do I apply for a study permit?")


# Test 3: Test filter answers with matching documents
def test_filter_answers_with_matches(agent):
    mock_docs = mock_response(200, {
        "results": {
            "matches": [
                {"score": 0.80, "metadata": {"text": "Apply for a study permit"}},
                {"score": 0.60, "metadata": {"text": "Low score document"}}
            ]
        }
    })
    
    filtered_answers = agent.filter_answers(mock_docs)
    expected_answers = [{"text": "Apply for a study permit"}]
    
    assert filtered_answers == expected_answers


# Test 4: Test filter answers when no matches are found
def test_filter_answers_no_matches(agent):
    mock_docs = mock_response(200, {
        "results": {
            "matches": []
        }
    })
    
    filtered_answers = agent.filter_answers(mock_docs)
    
    assert filtered_answers == "Answer not found"


# Test 5: Test combining matching documents' answers
def test_combine_matches_success(agent):
    filtered_answers = [
        {"text": "Apply for a study permit", "hyperlinks": ["link1"], "ref_link": "ref1"},
        {"text": "Eligibility criteria", "hyperlinks": ["link2"], "ref_link": "ref2"}
    ]
    
    combined_answers = agent.combine_matches(filtered_answers)
    
    expected_combined_answers = {
        "hyperlinks": ["link1", "link2"],
        "text": " Apply for a study permit Eligibility criteria",
        "ref_link": ["ref1", "ref2"]
    }
    
    assert combined_answers == expected_combined_answers


# Test 6: Test combining matching documents when no results found
def test_combine_matches_no_results(agent):
    combined_answers = agent.combine_matches("Answer not found")
    
    assert combined_answers == "Answer not found"


# Test 7: Test getting answers successfully
def test_get_answers_success(agent):
    mock_docs = mock_response(200, {
        "results": {
            "matches": [
                {"score": 0.80, "metadata": {"text": "Apply for a study permit", "hyperlinks": ["link1"], "ref_link": "ref1"}},
                {"score": 0.75, "metadata": {"text": "Eligibility criteria", "hyperlinks": ["link2"], "ref_link": "ref2"}}
            ]
        }
    })
    
    agent.pinecone.search = lambda *args, **kwargs: mock_docs
    result = agent.get_answers("How do I apply for a study permit?")
    
    expected_result = {
        "hyperlinks": ["link1", "link2"],
        "text": " Apply for a study permit Eligibility criteria",
        "ref_link": ["ref1", "ref2"]
    }
    
    assert result == expected_result


# Test 8: Test getting answers when no results are found
def test_get_answers_no_results(agent):
    mock_docs = mock_response(200, {
        "results": {
            "matches": []
        }
    })
    
    agent.pinecone.search = lambda *args, **kwargs: mock_docs
    result = agent.get_answers("Non-existing query")
    
    assert result == "Answer not found"

