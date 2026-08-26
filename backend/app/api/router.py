"""
app/api/router.py

Central router: registers all route modules.
Import this in main.py.
"""
from fastapi import APIRouter

from app.api.routes import learner, onboarding, skills, resources, recommendations, learning_history

api_router = APIRouter()

api_router.include_router(learner.router)
api_router.include_router(onboarding.router)
api_router.include_router(skills.router)
api_router.include_router(resources.router)
api_router.include_router(recommendations.router)
api_router.include_router(learning_history.router)
