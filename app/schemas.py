import decimal

import simplejson
from marshmallow import Schema, ValidationError, fields, validate, validates_schema

from app.constants import OperationStatuses, ReportFormats, WalletCurrencies


class CurrencyField(fields.Decimal):
    """ Custom field to make sure there maximum 2 digits after comma in decimal field"""

    def _validated(self, value):
        try:
            dec_value = decimal.Decimal(str(value))
        except (TypeError, ValueError, decimal.InvalidOperation):
            self.fail("invalid")
        if dec_value.as_tuple().exponent < -2:
            raise ValidationError("There should be maximum 2 digits after comma.")

        return super()._validated(value)


class StrictSchema(Schema):
    """ Make all schemas strict by default (as in marshmallow >= 3.0) """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("strict", True)
        super(StrictSchema, self).__init__(*args, **kwargs)

    class Meta:
        # Use simplejson to support Decimal rendering as JSON
        render_module = simplejson


class User(StrictSchema):
    name = fields.String(validate=validate.Length(min=1, max=1024), required=True)
    country = fields.String(validate=validate.Length(min=1, max=1024), required=True)
    city = fields.String(validate=validate.Length(min=1, max=1024), required=True)
    login = fields.String(validate=validate.Length(min=4, max=1024), required=True)
    password = fields.String(validate=validate.Length(min=4, max=1024), required=True)


class Registration(StrictSchema):
    user = fields.Nested(User, required=True)
    wallet_currency = fields.String(
        validate=validate.OneOf(WalletCurrencies.__members__), required=True
    )


class Money(StrictSchema):
    amount = CurrencyField(places=2, required=True)
    currency = fields.String(
        validate=validate.OneOf(WalletCurrencies.__members__), required=True
    )


class MoneyReceiverLogin(Money):
    receiver_login = fields.String(
        validate=validate.Length(min=4, max=1024), required=True
    )


class OperationStatus(StrictSchema):
    status = fields.String(
        validate=validate.OneOf(OperationStatuses.__members__), required=True
    )


class Report(StrictSchema):
    report_format = fields.String(
        validate=validate.OneOf(ReportFormats.__members__), required=True
    )
    date_from = fields.Date()
    date_to = fields.Date()

    user_login = fields.String()

    @validates_schema
    def validate_dates(self, data):
        if (
            "date_from" in data
            and "date_to" in data
            and data["date_from"] > data["date_to"]
        ):
            raise ValidationError(
                '"date_from" should be smaller than "date_to"', ["date_from", "date_to"]
            )
