import os
import json
import requests
from typing import Dict, Any, Optional
from gemini_cloud.engine.models import FunctorResult, Outcome, SpawnRequest

class VertexFunctor:
    """Probabilistic Functor using Vertex AI Gemini (via REST API)."""
    def __init__(self, project_id: str, location: str = "us-central1", model_id: str = "gemini-1.5-pro"):
        self.project_id = project_id
        self.location = location
        self.model_id = model_id
        self.api_endpoint = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/{model_id}:generateContent"

    def _get_access_token(self) -> Optional[str]:
        """Attempt to get an access token via gcloud or metadata server."""
        # This is a stub for getting the token in a real environment
        return os.environ.get("GOOGLE_ACCESS_TOKEN")

    def evaluate(self, candidate: str, context: Dict) -> FunctorResult:
        """Call Vertex AI to evaluate the candidate."""
        token = self._get_access_token()
        
        # Simulation if no token or project ID is placeholder
        if not token or self.project_id == "YOUR_PROJECT_ID" or "mock" in context:
            return self._simulate_evaluation(candidate, context)

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        prompt = self._build_prompt(candidate, context)
        payload = {
            "contents": {
                "role": "user",
                "parts": [{"text": prompt}]
            },
            "generationConfig": {
                "temperature": 0.2,
                "topP": 0.8,
                "topK": 40,
                "maxOutputTokens": 2048,
                "responseMimeType": "application/json"
            }
        }

        try:
            response = requests.post(self.api_endpoint, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            result_json = response.json()
            
            # Extract text from Gemini response
            # Note: This assumes responseMimeType: application/json was requested and supported
            content_text = result_json['candidates'][0]['content']['parts'][0]['text']
            data = json.loads(content_text)
            
            return FunctorResult(
                name="vertex_eval",
                outcome=Outcome.PASS if data.get("delta") == 0 else Outcome.FAIL,
                delta=data.get("delta", 1),
                reasoning=data.get("reasoning", "Vertex AI evaluation complete."),
                next_candidate=data.get("next_candidate", candidate),
                spawn=self._parse_spawn(data.get("spawn"))
            )
        except Exception as e:
            return FunctorResult(
                name="vertex_eval",
                outcome=Outcome.ERROR,
                delta=1,
                reasoning=f"Vertex AI API Error: {str(e)}",
                next_candidate=candidate
            )

    def _build_prompt(self, candidate: str, context: Dict) -> str:
        edge = context.get("edge", "unknown")
        feature_id = context.get("feature_id", "unknown")
        constraints = context.get("constraints", {})
        
        return f"""
        You are an expert software engineer implementing the AI SDLC methodology.
        Evaluate the current candidate for the feature '{feature_id}' on the edge '{edge}'.
        
        Constraints: {json.dumps(constraints)}
        
        Current Candidate:
        ---
        {candidate}
        ---
        
        Return a JSON object with:
        - "delta": 0 if converged, >0 if progress needed
        - "reasoning": detailed explanation of your evaluation
        - "next_candidate": the improved version of the candidate (if delta > 0)
        - "spawn": optional SpawnRequest if a new sub-feature is needed
        """

    def _simulate_evaluation(self, candidate: str, context: Dict) -> FunctorResult:
        """Heuristic evaluation for local development without GCP access."""
        edge = context.get("edge", "")
        is_valid = "Implements: REQ-" in candidate
        
        if is_valid:
            return FunctorResult(
                name="vertex_eval_sim",
                outcome=Outcome.PASS,
                delta=0,
                reasoning="[Simulated] Found traceability tags. Assuming convergence.",
                next_candidate=candidate
            )
        else:
            # Automatic fix in simulation
            next_candidate = f"# Implements: REQ-{context.get('feature_id', 'GEN')}-001\n" + candidate
            return FunctorResult(
                name="vertex_eval_sim",
                outcome=Outcome.FAIL,
                delta=1,
                reasoning="[Simulated] Missing traceability tags. Adding them.",
                next_candidate=next_candidate
            )

    def _parse_spawn(self, spawn_data: Optional[Dict]) -> Optional[SpawnRequest]:
        if not spawn_data:
            return None
        return SpawnRequest(
            question=spawn_data.get("question", "Unknown question"),
            vector_type=spawn_data.get("vector_type", "discovery")
        )
