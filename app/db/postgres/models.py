import sqlalchemy as sa

from app.constants import OperationStatuses, WalletCurrencies

metadata = sa.MetaData()

users = sa.Table(
    "users",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("name", sa.Unicode),
    sa.Column("country", sa.Unicode),
    sa.Column("city", sa.Unicode),
    sa.Column("login", sa.Unicode, unique=True, index=True),
    sa.Column("password", sa.Unicode),
)

wallets = sa.Table(
    "wallets",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column(
        "user_id",
        sa.Integer,
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True,
    ),
    sa.Column("amount", sa.DECIMAL(18, 2), nullable=False),
    sa.Column("currency", sa.Enum(WalletCurrencies), nullable=False),
)

operations = sa.Table(
    "operations",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column(
        "sender_wallet_id",
        sa.Integer,
        sa.ForeignKey("wallets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    sa.Column(
        "receiver_wallet_id",
        sa.Integer,
        sa.ForeignKey("wallets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    sa.Column("amount", sa.DECIMAL(18, 2), nullable=False),
    sa.Column("sender_wallet_rate", sa.DECIMAL(10, 2), nullable=False),
    sa.Column("receiver_wallet_rate", sa.DECIMAL(10, 2), nullable=False),
    sa.Column("datetime", sa.DateTime, nullable=False, index=True),
    sa.Column("signature", sa.Unicode, nullable=False),
)

operations_statuses = sa.Table(
    "operations_statuses",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column(
        "operation_id",
        sa.Integer,
        sa.ForeignKey("operations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    sa.Column("status", sa.Enum(OperationStatuses), nullable=False),
    sa.Column("datetime", sa.DateTime, nullable=False),
    sa.UniqueConstraint("operation_id", "status"),
)
