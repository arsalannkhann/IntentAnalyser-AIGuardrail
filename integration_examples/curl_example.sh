# Guardrail Integration Example - cURL

# Check user input
curl -X POST http://localhost:8000/intent \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Tell me about cURL",
    "role": "general"
  }'

# Expected response:
# {
#   "decision": "allow",
#   "intent": "info.query",
#   "risk_score": 0.1,
#   "tier": "P4_Info",
#   "confidence": 0.95,
#   "reason": "Safe information query"
# }
