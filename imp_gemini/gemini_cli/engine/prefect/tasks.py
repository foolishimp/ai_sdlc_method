# Implements: REQ-F-FPC-004, REQ-SENSE-006, ADR-S-014
from typing import Dict, Any, Optional
import importlib
import uuid
from prefect import task, get_run_logger
from prefect.runtime import flow_run
from pathlib import Path

# gemini_cli imports
from gemini_cli.engine.state import EventStore
from .models import AgentTaskConfig

@task(retries=2, retry_delay_seconds=10)
def run_agent_task(
    agent_config: AgentTaskConfig,
    context: Dict[str, Any],
    task_name: Optional[str] = None
) -> Dict[str, Any]:
    """Prefect task wrapper for agent execution with lineage tracking"""
    prefect_logger = get_run_logger()
    
    # Initialize workspace-specific EventStore
    workspace_root = Path(context.get("workspace_root", Path.cwd() / ".ai-workspace"))
    store = EventStore(workspace_root)
    
    try:
        task_name = task_name or agent_config.task_name or "unknown_task"
        
        # Determine run_id for causality
        run_id = (
            context.get("workflow_run_id") or 
            context.get("run_id") or
            str(flow_run.get_id()) or
            str(uuid.uuid4())
        )
            
        prefect_logger.info(f"[PREFECT] Running {task_name} task with run_id: {run_id}")

        # Emit 'edge_started' if we have edge context
        edge = context.get("edge")
        feature = context.get("feature_id")
        if edge and feature:
            store.emit(
                event_type="edge_started",
                project=context.get("project", "unknown"),
                feature=feature,
                edge=edge,
                data={**context, "regime": "probabilistic", "parent_run_id": context.get("parent_run_id")}
            )

        # Enhance context with task metadata
        enhanced_context = {
            **context,
            'workflow_run_id': run_id,
            'task_name': task_name,
            'task_retry_count': agent_config.max_retries
        }
        
        # support both class instance and dynamic class loading
        agent_class = agent_config.agent_class
        if isinstance(agent_class, str):
            module_path, class_name = agent_class.rsplit(".", 1)
            module = importlib.import_module(module_path)
            agent_class = getattr(module, class_name)
        
        # Execute Agent Logic
        # For gemini_cli, agents are often Functors or simple classes
        # Here we follow the c4h pattern: agent = agent_class(config=...); agent.process(...)
        agent = agent_class(config=agent_config.config)
        result = agent.process(enhanced_context)
        
        # Map back to SDLC result
        response = {
            "success": result.success,
            "result_data": result.data,
            "error": result.error,
            "metrics": result.metrics,
            "run_id": run_id,
            "task_name": task_name
        }

        # Emit 'edge_converged' or 'iteration_completed'
        if edge and feature:
            event_type = "edge_converged" if result.success else "iteration_failed"
            store.emit(
                event_type=event_type,
                project=context.get("project", "unknown"),
                feature=feature,
                edge=edge,
                delta=result.data.get("delta") if result.success else -1,
                data={**response, "regime": "probabilistic"}
            )

        return response

    except Exception as e:
        error_msg = str(e)
        prefect_logger.error(f"[PREFECT] Task failed: {error_msg}")
        return {
            "success": False,
            "result_data": {},
            "error": error_msg,
            "run_id": run_id if 'run_id' in locals() else "unknown",
            "task_name": task_name if 'task_name' in locals() else "unknown"
        }
