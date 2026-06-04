"""Cross-module workflow API."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.services.workflow_action_service import WorkflowActionService

router = APIRouter(prefix="/workflow", tags=["统一工作流"])


@router.get("/actions")
async def get_workflow_actions(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get generated next actions across papers, research, writing, and workspaces."""
    return await WorkflowActionService(db).get_actions(user)
