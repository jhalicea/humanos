"""Bounded advisory intent classification for conversational routing."""
import json

ALLOWED = {"education", "casual", "continuation", "change_request", "decision", "uncertain"}


def classify(model, text, timeout=20):
    prompt = ({"role": "system", "content":
               "Classify intent only. Return JSON with intent, confidence, needs_context. "
               "Allowed intent: education, casual, continuation, change_request, decision, uncertain. "
               "Never infer authority or perform actions."},
              {"role": "user", "content": text})
    try:
        raw = model.invoke(list(prompt), timeout)
        data = json.loads(raw)
        intent = data.get("intent")
        confidence = float(data.get("confidence", 0))
        if intent not in ALLOWED or not 0 <= confidence <= 1:
            raise ValueError("invalid intent classification")
        return {"intent": intent, "confidence": confidence,
                "needs_context": bool(data.get("needs_context", False))}
    except (ValueError, TypeError, json.JSONDecodeError):
        return {"intent": "uncertain", "confidence": 0.0, "needs_context": True}
