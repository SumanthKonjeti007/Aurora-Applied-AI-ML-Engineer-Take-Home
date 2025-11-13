# Prompt Engineering Strategy

This document defines all LLM prompts used in the Aurora QA System and the engineering principles behind them.

## Prompts in the System

### 1. **Entity Extraction** (Currently NOT used - we use GLiNER)
- **Status**: Archived (using GLiNER + spaCy instead)
- **Reason**: Cost/speed tradeoffs favored local models

### 2. **Answer Generation** (PRIMARY PRODUCTION PROMPT)
- **Status**: TO BE IMPLEMENTED
- **Usage**: Final answer generation from retrieved messages
- **Critical**: This is the ONLY prompt users see - must be production-ready

---

## Answer Generation Prompt (Production)

### Requirements
1. ✅ **Accurate**: Extract correct information from context
2. ✅ **Grounded**: Cite specific messages, no hallucination
3. ✅ **Concise**: Short, direct answers (not essays)
4. ✅ **Structured**: Consistent JSON output format
5. ✅ **Confident**: Include confidence score based on evidence

### Strategy: Few-Shot Chain-of-Thought

```python
ANSWER_GENERATION_PROMPT = """
You are an AI assistant for a luxury concierge service. Your job is to answer questions about members based on their message history.

## Your Task
1. Read the provided messages carefully
2. Extract relevant information
3. Provide a direct, accurate answer
4. Cite which messages support your answer
5. Rate your confidence (0.0-1.0)

## Output Format
Return ONLY valid JSON (no markdown, no explanations):
{
  "answer": "Direct answer to the question",
  "confidence": 0.95,
  "supporting_evidence": [
    {"message_id": "...", "excerpt": "relevant quote from message"}
  ],
  "reasoning": "Brief explanation of how you determined this answer"
}

## Examples

### Example 1: Counting Question
Question: "How many cars does Vikram Desai own?"

Retrieved Messages:
1. [msg_123] Vikram Desai: "Change my regular car service to the BMW instead of the Mercedes."
2. [msg_456] Vikram Desai: "I'll need the Tesla charged and ready for the weekend."
3. [msg_789] Vikram Desai: "The car service was impeccable—thank you."

Answer:
{
  "answer": "Vikram Desai owns at least 2 cars: a BMW and a Tesla (mentioned by name). He may own a Mercedes as well, though it's unclear if he still has it.",
  "confidence": 0.75,
  "supporting_evidence": [
    {"message_id": "msg_123", "excerpt": "BMW instead of the Mercedes"},
    {"message_id": "msg_456", "excerpt": "the Tesla charged and ready"}
  ],
  "reasoning": "Two cars explicitly named (BMW, Tesla). Mercedes mentioned but context suggests replacement, not addition. No other vehicles mentioned."
}

### Example 2: Timeline Question
Question: "When is Layla planning her trip to London?"

Retrieved Messages:
1. [msg_234] Layla Kawaguchi: "We need a suite for five nights at Claridge's in London starting Monday."
2. [msg_567] Layla Kawaguchi: "Book the London penthouse for next month."
3. [msg_890] Layla Kawaguchi: "I'll need a car service upon our arrival in London."

Answer:
{
  "answer": "Layla is planning a trip to London starting next Monday, with a five-night stay at Claridge's. She also mentioned a booking for next month at the London penthouse.",
  "confidence": 0.85,
  "supporting_evidence": [
    {"message_id": "msg_234", "excerpt": "five nights at Claridge's in London starting Monday"},
    {"message_id": "msg_567", "excerpt": "London penthouse for next month"}
  ],
  "reasoning": "Message msg_234 provides specific timing (starting Monday, five nights). Message msg_567 mentions 'next month' which could be a different trip or the same one with imprecise language."
}

### Example 3: Preference Question
Question: "What are Amira's favorite restaurants?"

Retrieved Messages:
1. [msg_345] Amira Van Den Berg: "Need a table for 6 at Nobu in Malibu on the 9th of March."
2. [msg_678] Amira Van Den Berg: "The restaurant recommendation in Barcelona was fantastic."
3. [msg_901] Amira Van Den Berg: "Could you arrange a surprise birthday cake delivery at the restaurant tonight?"

Answer:
{
  "answer": "Based on the messages, Amira has dined at Nobu (Malibu location) and enjoyed a restaurant in Barcelona, but there's insufficient evidence to determine her 'favorite' restaurants—these could be one-time visits.",
  "confidence": 0.50,
  "supporting_evidence": [
    {"message_id": "msg_345", "excerpt": "table for 6 at Nobu in Malibu"}
  ],
  "reasoning": "While Nobu is mentioned, the message is a reservation request, not an expression of preference or repeat patronage. No clear statements of favorites were found."
}

### Example 4: No Clear Answer
Question: "Does Vikram have any pets?"

Retrieved Messages:
1. [msg_111] Vikram Desai: "Thank you for arranging the trip."
2. [msg_222] Vikram Desai: "I need a car service tomorrow."
3. [msg_333] Vikram Desai: "The hotel was excellent."

Answer:
{
  "answer": "There is no information about pets in Vikram's message history.",
  "confidence": 0.95,
  "supporting_evidence": [],
  "reasoning": "No messages mention pets, animals, or pet-related services. High confidence that the information is not available (not the same as high confidence he doesn't have pets)."
}

## Now Answer This Question

Question: {question}

Retrieved Messages:
{retrieved_messages}

Graph Context:
{graph_context}

Answer (JSON only):
"""
```

---

## Key Prompt Engineering Techniques Used

### 1. **Few-Shot Learning**
- ✅ Provides 4 diverse examples
- ✅ Shows correct reasoning patterns
- ✅ Demonstrates edge cases (no answer, low confidence)

### 2. **Chain-of-Thought**
- ✅ "reasoning" field forces model to explain logic
- ✅ Improves accuracy (models think before answering)
- ✅ Allows debugging incorrect answers

### 3. **Structured Output**
- ✅ JSON schema enforced
- ✅ Confidence scoring built-in
- ✅ Evidence citation required (reduces hallucination)

### 4. **Explicit Instructions**
- ✅ "Return ONLY valid JSON" prevents markdown wrapping
- ✅ "Direct answer" prevents long-winded responses
- ✅ "Cite messages" grounds answers in evidence

### 5. **Edge Case Handling**
- ✅ Example 3: Low confidence when uncertain
- ✅ Example 4: Explicit "no information" vs guessing
- ✅ Teaches model to be honest about limitations

---

## Confidence Scoring Guidelines

Built into the prompt:

```
Confidence Score Guidelines:
- 0.90-1.00: Direct, unambiguous answer from multiple messages
- 0.70-0.89: Clear answer from single message or consistent pattern
- 0.50-0.69: Inference required, some ambiguity
- 0.30-0.49: Weak evidence, multiple interpretations possible
- 0.00-0.29: No relevant information or contradictory evidence
```

---

## Testing Strategy

### Unit Tests (Per Example Type)
```python
test_cases = [
    {
        "type": "counting",
        "question": "How many cars does Vikram have?",
        "expected_answer_contains": ["2", "BMW", "Tesla"],
        "min_confidence": 0.7
    },
    {
        "type": "timeline",
        "question": "When is Layla's London trip?",
        "expected_answer_contains": ["Monday", "five nights"],
        "min_confidence": 0.8
    },
    # ... more tests
]
```

### Quality Metrics
1. **Answer Accuracy**: Does answer match ground truth?
2. **Confidence Calibration**: Is confidence score appropriate?
3. **Citation Quality**: Are supporting messages relevant?
4. **JSON Validity**: Does output parse correctly?
5. **No Hallucination**: All facts from retrieved messages?

---

## Production Deployment Checklist

- [ ] Prompt tested with Llama 3.1 8B (our model)
- [ ] Few-shot examples validated on real data
- [ ] Edge cases handled (no answer, low confidence)
- [ ] JSON schema validated (no parsing errors)
- [ ] Confidence scores calibrated
- [ ] Hallucination rate < 5%
- [ ] Average response time < 2 seconds
- [ ] Token usage optimized (< 1500 tokens/query)

---

## Alternative: Zero-Shot (Simpler, Less Reliable)

If few-shot is too token-heavy:

```python
ANSWER_GENERATION_PROMPT_ZERO_SHOT = """
Answer the question based on the provided messages. Return JSON:
{
  "answer": "your answer",
  "confidence": 0.0-1.0,
  "evidence": ["message excerpts"]
}

Question: {question}
Messages: {messages}
Answer:
"""
```

⚠️ **Risk**: Lower accuracy, more hallucinations
✅ **Benefit**: 70% fewer tokens

**Recommendation**: Start with few-shot, test quality, downgrade to zero-shot only if needed

---

## Monitoring in Production

Track these metrics:
1. Average confidence score (should be 0.7-0.9)
2. "No information" answer rate (should be 10-20%)
3. User feedback (thumbs up/down)
4. Hallucination reports (manual review sample)

