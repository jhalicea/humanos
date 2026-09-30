import json

from intent_classifier import classify


class FakeModel:
    def __init__(self, response):
        self.response = response

    def invoke(self, messages, timeout):
        return self.response


def test_high_confidence_education_is_advisory():
    result = classify(FakeModel(json.dumps({"intent": "education", "confidence": 0.92,
                                            "needs_context": False})), "teach me what a runtime is")
    assert result["intent"] == "education"
    assert result["confidence"] == 0.92


def test_malformed_output_fails_closed():
    result = classify(FakeModel("not json"), "do something")
    assert result == {"intent": "uncertain", "confidence": 0.0, "needs_context": True}


def test_change_request_remains_distinct():
    result = classify(FakeModel('{"intent":"change_request","confidence":0.88,"needs_context":true}'), "edit the router")
    assert result["intent"] == "change_request"
