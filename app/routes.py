from aiohttp import web

from app.views import auth, operations, reports, wallet


def setup_routes(app: web.Application):
    app.router.add_routes(
        [
            # auth
            web.post(r"/api/auth/signup", auth.signup),
            web.post(r"/api/auth/login", auth.login),
            # wallet balance
            web.post(r"/api/wallet/balance", wallet.put_money_on_balance),
            web.get(r"/api/wallet/balance", wallet.get_balance),
            # wallet operations
            web.post(r"/api/wallet/operations", wallet.create_operation),
            # operations statuses
            web.post(r"/api/operations/{operation_id:\d+}", operations.change_status),
            # reports
            web.get(r"/api/report/operations", reports.get_report_operations),
            web.get(r"/api/report/statuses", reports.get_report_statuses),
        ]
    )
