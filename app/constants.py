from enum import Enum


class WalletCurrencies(str, Enum):
    USD = "USD"
    EUR = "EUR"
    CAD = "CAD"
    CNY = "CNY"


class OperationStatuses(str, Enum):
    DRAFT = "DRAFT"
    PROCESSING = "PROCESSING"
    ACCEPTED = "ACCEPTED"
    FAILED = "FAILED"

    def __str__(self):
        """ For correct formatting in reports """
        return self.value


class ReportFormats(str, Enum):
    XML = "XML"
    CSV = "CSV"


class ReportTypes(str, Enum):
    OPERATIONS = "operations"
    STATUSES = "statuses"


# Allowed transactions between operation states
ALLOWED_TRANSACTIONS = {
    OperationStatuses.DRAFT: [OperationStatuses.PROCESSING, OperationStatuses.FAILED],
    OperationStatuses.PROCESSING: [
        OperationStatuses.ACCEPTED,
        OperationStatuses.FAILED,
    ],
    OperationStatuses.ACCEPTED: [],
    OperationStatuses.FAILED: [],
}
