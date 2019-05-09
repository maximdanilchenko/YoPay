

async def test_registration(cli, user1, select_user):
    resp = await cli.post('/api/auth/signup', json={
        "user": user1,
        "wallet_currency": "USD"
    })
    assert resp.status == 200
    user = await select_user(user1["login"])
    assert user
    user = dict(user)
    assert user["login"] == user1["login"]
    assert user["city"] == user1["city"]
    assert user["country"] == user1["country"]
    assert user["name"] == user1["name"]


async def test_login(cli, create_users, user1):
    resp = await cli.post('/api/auth/login', json={
        "password": user1["password"],
        "login": user1["login"],
    })
    assert resp.status == 200
    assert "token" in await resp.json()
