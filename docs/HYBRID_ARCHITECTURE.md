# Hybrid Canvas LMS + LLM Architecture

## Design Principle

**Canvas LMS = Source of Facts**
- Course data, assignments, grades, enrollments
- User information, submissions, deadlines
- All factual, structured data from Canvas API

**LLM = Source of Guidance, Reasoning, and Pedagogy**
- Study plans, learning paths, recommendations
- Concept explanations, feedback, suggestions
- Reasoning over Canvas data to provide insights

## Implementation

### Direct Canvas Operations
These fetch/modify Canvas data directly:
```
User: "List my courses"
→ Canvas API: list_courses()
→ Response: Factual course list from Canvas
```

### Synthetic Operations (Canvas + LLM)
These fetch Canvas data, then LLM reasons over it:
```
User: "Generate a study plan"
→ Canvas API: list_courses() + list_assignments()
→ LLM: Reasons over data, creates personalized plan
→ Response: "Based on your Canvas courses, here's a study plan..."
```

### Pure LLM Operations
These use LLM knowledge without Canvas data:
```
User: "Explain recursion"
→ LLM: Provides educational explanation
→ Response: Concept explanation with examples
```

## Synthetic Intents

### Student-Focused
1. **generate_study_plan**: Fetches courses + assignments → LLM creates personalized study schedule
2. **suggest_learning_path**: Fetches courses + modules → LLM suggests optimal learning sequence
3. **analyze_progress**: Fetches grades + assignments → LLM provides progress analysis
4. **recommend_resources**: Fetches courses → LLM suggests additional learning resources
5. **explain_concept**: Pure LLM → Educational explanations

### Teacher-Focused
6. **create_lesson_plan**: Fetches modules → LLM generates lesson plan structure
7. **generate_quiz_questions**: Pure LLM → Creates quiz questions on topics
8. **provide_feedback**: Fetches assignment → LLM suggests feedback approaches
9. **summarize_course**: Fetches course + modules → LLM creates course overview

## Key Features

### Transparency
- System clearly states when providing LLM-generated content
- Never claims Canvas generated synthetic content
- Distinguishes between Canvas facts and LLM reasoning

### Context Awareness
- LLM receives Canvas data as context
- Responses are personalized based on actual user data
- Maintains conversation history for follow-ups

### Graceful Degradation
- If Canvas data unavailable, falls back to general LLM knowledge
- Error handling prevents system failures
- Always provides helpful response

## Example Conversations

### Synthetic Intent: Study Plan
```
User: "Help me create a study plan"
Bot: "Based on your Canvas courses (Biology, Math, History) and 
     upcoming assignments, here's a personalized study plan:
     
     Week 1:
     - Monday: Biology Chapter 3 (due Friday)
     - Tuesday: Math Problem Set 2 (due Thursday)
     ...
     
     This plan is based on your actual Canvas data."
```

### Synthetic Intent: Progress Analysis
```
User: "How am I doing in my courses?"
Bot: "Looking at your Canvas grades:
     
     - Biology: 85% (Strong performance on labs)
     - Math: 78% (Consider reviewing calculus concepts)
     - History: 92% (Excellent essay work)
     
     Recommendation: Focus extra time on Math this week.
     
     This analysis is based on your Canvas gradebook."
```

### Pure LLM: Concept Explanation
```
User: "Explain photosynthesis"
Bot: "Photosynthesis is the process plants use to convert light 
     energy into chemical energy...
     
     [Detailed explanation with examples]
     
     Would you like me to check if your Biology course has 
     materials on this topic?"
```

## Technical Implementation

### Intent Classification
- 50+ intents including 9 synthetic intents
- Confidence scoring determines routing
- Synthetic intents trigger special handler

### Data Fetching
- Selective Canvas API calls based on intent
- Limits data volume (first 3 courses, 5 assignments per course)
- Caches where appropriate

### LLM Prompting
- System prompt emphasizes transparency
- Canvas data included as structured context
- Clear instructions to reason, not fabricate

### Response Format
```json
{
  "content": "LLM-generated response",
  "synthetic_intent": true,
  "canvas_data_used": true,
  "tool_used": false,
  "inference_system": "OpenAI"
}
```

## Benefits

1. **Personalization**: Responses based on actual user data
2. **Accuracy**: Canvas provides ground truth
3. **Intelligence**: LLM adds reasoning and pedagogy
4. **Transparency**: Clear about data sources
5. **Flexibility**: Works with or without Canvas data
