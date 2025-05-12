"""Organisations related REST routes."""

from sanic import Blueprint, Request

organisations_bp = Blueprint("organisations")


@organisations_bp.route("/organisations/", methods=["GET"])
async def list_organisations(request: Request): ...


@organisations_bp.route("/organisations/<organisation_id:int>", methods=["GET"])
async def get_organisation(request: Request, organisation_id): ...


@organisations_bp.route("/organisations", methods=["POST"])
async def create_organisation(request: Request): ...


@organisations_bp.route("/organisations/<organisation_id:int>", methods=["PUT"])
async def update_organisation(request: Request, organisation_id): ...
