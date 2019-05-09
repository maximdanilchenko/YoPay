async def test_get_balance(cli, create_users, user1, wallet_selector, user_authorizer):
    resp = await cli.get("/api/wallet/balance", headers=await user_authorizer(user1))
    assert resp.status == 200
    assert await resp.json() == dict(await wallet_selector(user1))
