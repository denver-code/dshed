from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime
from app.core.authorization import auth_required
from beanie import PydanticObjectId, Document
from enum import Enum

private_router = APIRouter(
    prefix="/private",
    tags=["private"],
    dependencies=[
        Depends(auth_required),
    ],
)


@private_router.get("/")
async def private_root():
    return {
        "message": "Hello in Private World",
        "latest_version": "v1",
    }


document_router = APIRouter(
    prefix="/document",
    tags=["document"],
    dependencies=[
        Depends(auth_required),
    ],
)


class DocumentPicture(BaseModel):
    back: bytes
    front: bytes


# scope
class DocumentModel(Document):
    title: str
    description: str
    owner: str
    content: dict
    picture: Optional[DocumentPicture] = None
    is_critical: bool
    metadata: dict = {}

    class Settings:
        name = "documents"


class BacklogModel(Document):
    document_requested_id: PydanticObjectId
    owner: str
    time_requested: datetime

    class Settings:
        name = "backlog"


class NewDocumentSchema(BaseModel):
    title: str
    description: str
    content: dict
    is_critical: bool


# enum of states
class DocumentStateEnum(str, Enum):
    STORED = "Stored"
    USING = "Using"
    LOST = "Lost"
    EXPIRED = "Expired"

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_


class DocumentState(Document):
    document_id: PydanticObjectId
    owner: str
    state: DocumentStateEnum
    time: datetime


@document_router.get("/")
async def document_root():
    return {
        "message": "Hello in Document World",
        "latest_version": "v1",
    }


@document_router.get("/all")
async def get_documents(user=Depends(auth_required)):
    # return await DocumentModel.find({"owner": user["sub"]}).to_list()
    _documents = await DocumentModel.find({"owner": user["sub"]}).to_list()
    documents = []
    for document in _documents:
        document = document.dict()
        to_del = ["content", "owner", "picture", "metadata"]
        for key in to_del:
            del document[key]
        documents.append(document)

    return documents


@document_router.get("/{document_id}/state")
async def get_document_state(
    document_id: PydanticObjectId, user=Depends(auth_required)
):
    document = await DocumentModel.find_one({"_id": document_id, "owner": user["sub"]})
    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    state = await DocumentState.find_one(
        {"document_id": document_id, "owner": user["sub"]}
    )
    if not state:
        raise HTTPException(
            status_code=404,
            detail="Document state not found",
        )

    return state


@document_router.put("/{document_id}/state")
async def update_document_state(
    document_id: PydanticObjectId, user=Depends(auth_required), state: str = None
):
    if not state:
        raise HTTPException(
            status_code=400,
            detail="State is required",
        )

    if not DocumentStateEnum.has_value(state):
        raise HTTPException(
            status_code=400,
            detail="Invalid state",
        )

    document = await DocumentModel.find_one({"_id": document_id, "owner": user["sub"]})

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    d_state = await DocumentState.find_one(
        {"document_id": document_id, "owner": user["sub"]}
    )

    if not d_state:
        raise HTTPException(
            status_code=404,
            detail="Document state not found",
        )

    d_state.state = DocumentStateEnum(state)
    d_state.time = datetime.utcnow()

    await d_state.save()

    return {
        "message": "Document state updated successfully",
    }


@document_router.delete("/{document_id}")
async def delete_document(document_id: PydanticObjectId, user=Depends(auth_required)):
    document = await DocumentModel.find_one({"_id": document_id, "owner": user["sub"]})
    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    await BacklogModel.find(
        {"document_requested_id": document_id, "owner": user["sub"]}
    ).delete()

    await DocumentState.find(
        {"document_id": document_id, "owner": user["sub"]}
    ).delete()

    await document.delete()
    return {
        "message": "Document deleted successfully",
    }


@document_router.get("/{document_id}")
async def get_document(document_id: PydanticObjectId, user=Depends(auth_required)):
    document = await DocumentModel.find_one({"_id": document_id, "owner": user["sub"]})
    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    await BacklogModel.insert_one(
        BacklogModel(
            document_requested_id=document_id,
            time_requested=datetime.utcnow(),
            owner=user["sub"],
        )
    )

    return document


@document_router.post("/add")
async def add_document(payload: NewDocumentSchema, user=Depends(auth_required)):
    if await DocumentModel.find_one({"content": payload.content, "owner": user["sub"]}):
        raise HTTPException(
            status_code=400,
            detail="Document with this title already exists",
        )
    document = DocumentModel(**payload.model_dump(), owner=user["sub"])
    await document.insert()

    state = DocumentState(
        document_id=document.id,
        owner=user["sub"],
        state=DocumentStateEnum.STORED,
        time=datetime.utcnow(),
    )

    await state.insert()

    return {
        "message": "Document added successfully",
    }


private_router.include_router(document_router)

backlog_router = APIRouter(
    prefix="/backlog",
    tags=["backlog"],
    dependencies=[
        Depends(auth_required),
    ],
)


@backlog_router.get("/all")
async def get_backlog(user=Depends(auth_required)):
    return await BacklogModel.find({"owner": user["sub"]}).to_list()


private_router.include_router(backlog_router)
