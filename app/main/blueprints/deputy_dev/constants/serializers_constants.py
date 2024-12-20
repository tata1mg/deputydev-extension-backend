from enum import Enum


class SerializerTypes(Enum):
    PRS_SERIALIZER = "PrsSerializer"
    SHADCN = "shadcn"


class CommentDeeplinks(Enum):
    BITBUCKET = "https://bitbucket.org/{workspace}/{repo}/pull-requests/{pr_id}#comment-{comment_id}"
    GITHUB = "https://github.com/{workspace}/{repo}/pull/{pr_id}/files#r{comment_id}"
