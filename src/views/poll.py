from enum import StrEnum

from fastapi import APIRouter, Security
from fastapi_jwt import JwtAuthorizationCredentials
from sqlalchemy.orm import Session

import src.database as database
from . import schemas
from fastapi import Depends, FastAPI, HTTPException

from ..config import jwt_config
from ..database.scripts import poll as db_poll

router = APIRouter(prefix='/poll', tags=['Polls'])

@router.post('/create',
             response_model=schemas.Poll)
def create_poll(poll: schemas.PollCreate,
                db: Session = Depends(database.utils.get_session),
                credentials: JwtAuthorizationCredentials = Security(jwt_config.access_security)):
    user_id = credentials.subject["id"]
    try:
        return schemas.Poll.model_validate(db_poll.create.execute(db, user_id=user_id, **poll.__dict__))
    except db_poll.create.document_not_found:
            raise HTTPException(status_code=404)
    except db_poll.create.no_constraints:
        raise HTTPException(status_code=400)


@router.get('/created_by_me',
            response_model=list[schemas.Poll])
def get_my_polls(db: Session = Depends(database.utils.get_session),
                 credentials: JwtAuthorizationCredentials = Security(jwt_config.access_security)):
    user_id = credentials.subject["id"]
    return [schemas.Poll.model_validate(i) for i in db_poll.by_user.execute(db, user_id=user_id)]

@router.get('/for_group',
            response_model=list[schemas.Poll])
def get_polls_for_group(group_id:int,
                 db: Session = Depends(database.utils.get_session),
                 credentials: JwtAuthorizationCredentials = Security(jwt_config.access_security)):
    user_id = credentials.subject["id"]
    try:
        return [schemas.Poll.model_validate(i) for i in db_poll.for_group.execute(db, user_id, group_id)]
    except db_poll.for_group.not_in_group:
        raise HTTPException(status_code=400)

@router.get('/info',
            response_model=schemas.RestrictedPoll)
def get_poll_info(poll_id:int,
                  db: Session = Depends(database.utils.get_session)):
    try:
        return schemas.RestrictedPoll.model_validate(db_poll.safe_get_poll_by_id.execute(db, poll_id))
    except db_poll.safe_get_poll_by_id.poll_not_found:
        raise HTTPException(status_code=404)