from aiohttp import web
from aiohttp_apispec import docs, request_schema

from app.constants import ReportTypes
from app.decorators import authorized_user
from app.report_builder import make_report_builder
from app.schemas import Report


@docs(tags=["reports"], security={"auth": []}, summary="Operations report generating")
@authorized_user(allow_unauthorized=True)
@request_schema(Report, locations=["query"])
async def get_report_operations(request: web.Request) -> web.StreamResponse:
    report_builder = make_report_builder(
        request, request["data"]["report_format"], ReportTypes.OPERATIONS
    )
    return await report_builder.build_report_response()


@docs(tags=["reports"], security={"auth": []}, summary="Statuses report generating")
@authorized_user(allow_unauthorized=True)
@request_schema(Report, locations=["query"])
async def get_report_statuses(request: web.Request) -> web.StreamResponse:
    report_builder = make_report_builder(
        request, request["data"]["report_format"], ReportTypes.STATUSES
    )
    return await report_builder.build_report_response()
