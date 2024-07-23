import contextvars

"""
This module defines context variables for the deputy_dev blueprint.
Context Variables:
    identifier (ContextVar): A context variable for storing the repository name to prefix Redis cache keys.
"""
identifier = contextvars.ContextVar("identifier")
