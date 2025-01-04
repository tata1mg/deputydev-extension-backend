import contextvars

"""
Context Variables:
    identifier (ContextVar): A context variable for storing the repository name to prefix Redis cache keys.
"""
identifier = contextvars.ContextVar("identifier")
