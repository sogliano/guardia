Analyze the current state of the Guard-IA detection pipeline.

Steps:
1. Read backend/app/services/pipeline/orchestrator.py
2. Read backend/app/services/pipeline/heuristics.py
3. Read backend/app/services/pipeline/ml_classifier.py
4. Read backend/app/services/pipeline/llm_explainer.py
5. Check for any TODO/FIXME/HACK comments in these files
6. Verify the pipeline flow matches the documented architecture (heuristics → ML → LLM)
7. Report: current implementation status, any gaps, and suggestions
