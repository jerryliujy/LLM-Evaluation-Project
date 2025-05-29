You need to evaluate the quality of a candidate answer to a Linux kernel-related question. Provided information includes:
- question: The question being asked
- reference_answer: The correct answer
- key_points: Key knowledge points from the reference answer (numbered)
- candidate_answer: The answer to be evaluated

### Your Task

Analyze the candidate answer and output a strictly formatted JSON evaluation result containing the following fields:

- `"key_points_evaluation"`: An object containing:
  - `"missed"`: Key point numbers absent from the answer
  - `"partial"`: Key point numbers mentioned but lacking details
  - `"matched"`: Key point numbers fully covered

For each of the following fields, you MUST use exact, unmodified text from the candidate answer:
- `"factual_errors"`: List of factually incorrect statements
- `"vague_statements"`: List of ambiguous statements
- `"partially_correct_but_misleading"`: List of misleading statements
- `"irrelevant_but_correct"`: List of irrelevant statements

Each item in these lists must contain:
- `"exact_text"`: The exact text copied from the answer (DO NOT modify or summarize)
- `"explanation"`: Brief explanation of the issue

### Important Rules: Reference Original Text

1. Reference text must be exact:
   - Text must be copied directly from the answer, without modification
   - No summarizing, paraphrasing, or adding/removing words
   - No changing punctuation or formatting
   - If text spans multiple sentences, include complete sentences

2. Reference must be continuous:
   - Text must be a continuous segment from the answer
   - If multiple parts need to be referenced, create separate entries
   - Do not combine or concatenate text from different parts of the answer

### Example Input

```json
{
  "question": "How does the Linux kernel handle process scheduling?",
  "reference_answer": "The Linux kernel uses the Completely Fair Scheduler (CFS) as the default scheduler. CFS manages processes using a red-black tree (RB-Tree) and determines process priority based on vruntime. Additionally, the Linux kernel provides real-time scheduling policies such as SCHED_FIFO and SCHED_RR to meet different scheduling needs.",
  "key_points": {
    "1": "The Linux kernel uses CFS as the default scheduler",
    "2": "CFS manages processes using a red-black tree (RB-Tree)",
    "3": "CFS determines process priority based on vruntime",
    "4": "The Linux kernel provides real-time scheduling policies such as SCHED_FIFO and SCHED_RR"
  },
  "candidate_answer": "Linux uses Completely Fair Scheduler(CFS) for scheduling, and CFS allocates CPU time using time slices. Linux employs a certain data structure to manage processes. Additionally, Linux supports BPF for flexible scheduling."
}
```

### Example Output

Only output the JSON object, no other text or comments.

```json
{
  "key_points_evaluation": {
    "missed": [3, 4],
    "partial": [2],
    "matched": [1]
  },
  "factual_errors": [
    {
      "exact_text": "CFS allocates CPU time using time slices",
      "explanation": "CFS does not use time slices, it uses vruntime for fair scheduling"
    }
  ],
  "vague_statements": [
    {
      "exact_text": "Linux employs a certain data structure to manage processes",
      "explanation": "The statement is vague as it does not specify which data structure (red-black tree) is used"
    }
  ],
  "partially_correct_but_misleading": [],
  "irrelevant_but_correct": [
    {
      "exact_text": "Linux supports BPF for flexible scheduling",
      "explanation": "While BPF can be used for scheduling, it is not directly related to the core scheduling mechanisms being discussed"
    }
  ]
}
```