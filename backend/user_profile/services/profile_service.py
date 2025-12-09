"""User profile service for managing session state."""
from typing import List, Optional
from fastapi import Request
from backend.user_profile.models.profile import UserProfile, IncorrectConceptRef


def get_user_profile(request: Request) -> UserProfile:
    """Get user profile from session, creating default if not exists."""
    if "user_profile" not in request.session:
        request.session["user_profile"] = UserProfile().model_dump()
    return UserProfile(**request.session["user_profile"])


def set_user_profile(request: Request, profile: UserProfile) -> None:
    """Update user profile in session."""
    request.session["user_profile"] = profile.model_dump()


def set_rating(request: Request, rating: float) -> UserProfile:
    """Set user rating in profile."""
    profile = get_user_profile(request)
    profile.rating = rating
    set_user_profile(request, profile)
    return profile


def update_rating(request: Request, rating: float) -> UserProfile:
    """Update user rating in profile."""
    profile = get_user_profile(request)
    profile.rating = rating
    set_user_profile(request, profile)
    return profile


def set_incorrect_concepts(request: Request, concepts: List[IncorrectConceptRef]) -> UserProfile:
    """Store concepts answered incorrectly for the latest quiz."""
    profile = get_user_profile(request)
    profile.incorrect_concepts = concepts
    set_user_profile(request, profile)
    return profile

