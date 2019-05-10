import csv
from abc import ABC, abstractmethod
from xml.etree.ElementTree import Element, tostring

import sqlalchemy as sa
from aiohttp import web
from databases import Database

from app.constants import OperationStatuses, ReportFormats, ReportTypes
from app.db.postgres.models import operations, operations_statuses, users, wallets
from app.utils import json_response

__all__ = ["make_report_builder"]


def make_report_builder(request, report_format, report_type):
    """
    Returns needed ReportBuilder subclass based on report_format and report_type.
    """
    builder = {
        ReportFormats.CSV: CSVReportBuilder,
        ReportFormats.XML: XMLReportBuilder,
    }[report_format]
    return builder(request, report_type)


class BytesStream:
    def write(self, string: str) -> bytes:
        return string.encode()


class ReportBuilder(ABC):
    def __init__(self, request, report_type):
        self.request = request
        self.db: Database = request.app["db"]
        self.user_id = request.get("user_id")
        self.query_params = request["data"]
        self.report_type = report_type

    @property
    @abstractmethod
    def content_type(self) -> str:
        """ "Content-Type" header value """
        ...

    @abstractmethod
    async def stream_report(self, response: web.StreamResponse, query):
        """ Actual streaming """
        ...

    async def build_report_response(self) -> web.StreamResponse:
        """ Stream report file to client without saving whole file in memory """

        if not self.user_id:  # If it is not authorized request
            try:
                login = self.query_params["user_login"]
            except KeyError:
                return json_response({"user_login": "Required field"}, status=422)
            user_id = await self.db.fetch_val(
                sa.select([users.c.id]).where(users.c.login == login)
            )
            if not user_id:
                return json_response({}, status=404, error="User not found")
            self.user_id = user_id

        # Building query based on report type
        query = build_report_query(
            self.user_id,
            self.report_type,
            date_from=self.query_params.get("date_from"),
            date_to=self.query_params.get("date_to"),
        )

        # Preparing streaming response
        response = web.StreamResponse(
            status=200, headers={"Content-Type": self.content_type}
        )
        await response.prepare(self.request)

        await self.stream_report(response, query)

        await response.write_eof()
        return response


class XMLReportBuilder(ReportBuilder):
    REPORT_TAG_MAP = {
        ReportTypes.OPERATIONS: (b"operations", "operation"),
        ReportTypes.STATUSES: (b"statuses", "status"),
    }

    @property
    def content_type(self) -> str:
        return "text/xml"

    async def stream_report(self, response: web.StreamResponse, query):

        main_tag, one_tag = self.REPORT_TAG_MAP[self.report_type]

        await response.write(
            b'<?xml version="1.0" encoding="windows-1251"?>\n<%s>\n' % main_tag
        )
        async with self.db.transaction():
            async for record in self.db.iterate(query):
                await response.write(self.dict_to_xml(one_tag, record) + b"\n")
        await response.write(b"</%s>\n" % main_tag)

    @staticmethod
    def dict_to_xml(tag, d):
        elem = Element(tag)
        for key, val in d.items():
            child = Element(key)
            child.text = str(val)
            elem.append(child)
        return tostring(elem)


class CSVReportBuilder(ReportBuilder):
    ROW_NAMES_MAP = {
        ReportTypes.OPERATIONS: [
            "id",
            "amount",
            "datetime",
            "signature",
            "sender_login",
            "receiver_login",
            "type",
        ],
        ReportTypes.STATUSES: ["id", "status"],
    }

    @property
    def content_type(self) -> str:
        return "text/csv"

    async def stream_report(self, response: web.StreamResponse, query):
        writer = csv.writer(BytesStream())
        await response.write(writer.writerow(self.ROW_NAMES_MAP[self.report_type]))
        async with self.db.transaction():
            async for record in self.db.iterate(query):
                await response.write(writer.writerow(record.values()))


def build_report_query(user_id, report_type, date_from=None, date_to=None):
    # query
    if report_type == ReportTypes.STATUSES:
        query = build_statuses_query(user_id)
    else:
        query = build_operations_query(user_id)
    # filters
    if date_from:
        query = query.where(operations.c.datetime >= date_from)
    if date_to:
        query = query.where(operations.c.datetime < date_to)
    return query


def build_operations_query(user_id):
    senders = sa.alias(users)
    receivers = sa.alias(users)

    sender_wallets = sa.alias(wallets)
    receiver_wallets = sa.alias(wallets)

    # query
    return (
        sa.select(
            [
                operations.c.id,
                operations.c.amount,
                operations.c.datetime,
                operations.c.signature,
                senders.c.login.label("sender_login"),
                receivers.c.login.label("receiver_login"),
                sa.case(
                    [
                        (sender_wallets.c.user_id == user_id, "outcome"),
                        (receiver_wallets.c.user_id == user_id, "income"),
                    ]
                ).label("type"),
            ]
        )
        .select_from(
            operations.join(
                sender_wallets, operations.c.sender_wallet_id == sender_wallets.c.id
            )
            .join(senders, sender_wallets.c.user_id == senders.c.id)
            .join(
                receiver_wallets,
                operations.c.receiver_wallet_id == receiver_wallets.c.id,
            )
            .join(receivers, receiver_wallets.c.user_id == receivers.c.id)
            .join(
                operations_statuses,
                sa.and_(
                    operations_statuses.c.operation_id == operations.c.id,
                    operations_statuses.c.status == OperationStatuses.ACCEPTED,
                ),
            )
        )
        .where(
            sa.or_(
                sender_wallets.c.user_id == user_id,
                receiver_wallets.c.user_id == user_id,
            )
        )
    )


def build_statuses_query(user_id):

    sender_wallets = sa.alias(wallets)
    receiver_wallets = sa.alias(wallets)

    # query
    return (
        sa.select(
            [
                operations.c.id.label("operation_id"),
                operations_statuses.c.status.label("value"),
                operations_statuses.c.datetime.label("datetime"),
            ]
        )
        .select_from(
            operations_statuses.join(operations)
            .join(sender_wallets, operations.c.sender_wallet_id == sender_wallets.c.id)
            .join(
                receiver_wallets,
                operations.c.receiver_wallet_id == receiver_wallets.c.id,
            )
        )
        .where(
            sa.or_(
                sender_wallets.c.user_id == user_id,
                receiver_wallets.c.user_id == user_id,
            )
        )
        .order_by(operations.c.id.desc(), operations_statuses.c.id.desc())
    )
