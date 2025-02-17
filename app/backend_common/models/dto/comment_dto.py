from pydantic import BaseModel


class CommentDTO(BaseModel):
    scm_comment_id: int
    body: str
