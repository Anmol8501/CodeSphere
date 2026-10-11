"""Topics, tags and the DSA learning path (any signed-in user)."""

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import ApiResponse, ErrorResponse, ok
from app.schemas.learning import LearningPath, TopicDetail, TopicOut
from app.schemas.problem import TagOut
from app.services import learning_service, tag_service, topic_service

router = APIRouter(
    tags=["Learning"],
    dependencies=[Depends(get_current_user)],
    responses={401: {"model": ErrorResponse}},
)


@router.get("/topics", response_model=ApiResponse[list[TopicOut]], summary="Topics in learning-path order")
def list_topics(db: Session = Depends(get_db)):
    counts = topic_service.published_counts_by_topic(db)
    topics = [topic_service.to_topic_out(t, counts.get(t.id, 0)) for t in topic_service.list_topics(db)]
    return ok("Topics retrieved", topics)


@router.get(
    "/topics/{slug}",
    response_model=ApiResponse[TopicDetail],
    summary="Topic details with problem counts and your progress",
    responses={404: {"model": ErrorResponse}},
)
def get_topic(
    slug: str = Path(max_length=80),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ok("Topic retrieved", learning_service.get_topic_detail(db, slug, user))


@router.get("/tags", response_model=ApiResponse[list[TagOut]], summary="All problem tags")
def list_tags(db: Session = Depends(get_db)):
    return ok("Tags retrieved", [TagOut.model_validate(t) for t in tag_service.list_tags(db)])


@router.get(
    "/learning-path",
    response_model=ApiResponse[LearningPath],
    summary="Ordered topics with problem counts and your progress",
)
def learning_path(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ok("Learning path", learning_service.build_learning_path(db, user))
