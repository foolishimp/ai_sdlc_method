# Implements: REQ-F-FPC-004, REQ-EDGE-001, REQ-EDGE-002, REQ-EDGE-003, REQ-EDGE-004
from prefect import flow, get_run_logger
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime, timezone
import uuid

from .tasks import run_agent_task
from .models import AgentTaskConfig

@flow(name="sdlc_edge_iteration")
def run_sdlc_workflow(
    edge: str,
    feature_id: str,
    asset_path: Path,
    context: Dict[str, Any],
    agent_class: Any,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Prefect flow representing an SDLC edge iteration.
    Allows for long-running, asynchronous, and recoverable agent execution.
    """
    logger = get_run_logger()
    
    # Generate Workflow ID (Correlation ID)
    workflow_id = str(uuid.uuid4())
    logger.info(f"[PREFECT] Initialized workflow {workflow_id} for edge {edge} on feature {feature_id}")
    
    # Prepare Agent Configuration
    agent_task_config = AgentTaskConfig(
        agent_class=agent_class,
        config=config,
        task_name=f"{edge}_agent",
        requires_approval=True if "design" in edge or "code" in edge else False,
        max_retries=2,
        retry_delay_seconds=60
    )
    
    # Prepare Task Context
    task_context = {
        **context,
        "edge": edge,
        "feature_id": feature_id,
        "asset_path": str(asset_path),
        "workflow_run_id": workflow_id,
        "workspace_root": str(context.get("workspace_root", Path.cwd() / ".ai-workspace"))
    }
    
    # Run the Agent Task
    result = run_agent_task(
        agent_config=agent_task_config,
        context=task_context
    )
    
    # Return comprehensive workflow result
    return {
        "status": "success" if result.get("success") else "error",
        "workflow_id": workflow_id,
        "edge": edge,
        "feature_id": feature_id,
        "result_data": result.get("result_data"),
        "error": result.get("error"),
        "metrics": result.get("metrics", {}),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
