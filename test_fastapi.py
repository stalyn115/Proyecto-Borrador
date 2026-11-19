import sys
from fastapi import FastAPI, Form
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

class LoginRequest(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    usuario: Optional[str] = None
    clave: Optional[str] = None

@app.post('/login')
async def login(
    data: LoginRequest | None = None,
    username: str | None = Form(default=None),
    password: str | None = Form(default=None)
):
    user = (data.username or data.usuario if data else username) or ""
    pwd = (data.password or data.clave if data else password) or ""
    return {'user': user, 'pwd': pwd}

from starlette.requests import Request
import asyncio

async def test():
    # simulate json request
    import json
    from starlette.datastructures import Headers
    
    scope = {
        'type': 'http',
        'method': 'POST',
        'path': '/login',
        'headers': [(b'content-type', b'application/json')],
    }
    body = json.dumps({'username': 'testuser', 'password': 'testpass'}).encode('utf-8')
    
    async def receive():
        return {'type': 'http.request', 'body': body, 'more_body': False}
    
    # Let's call using httpx AsyncClient
    import httpx
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        r1 = await client.post('/login', json={'username': 'testuser', 'password': 'testpass'})
        print("STATUS JSON:", r1.status_code)
        print("BODY JSON:", r1.text)

        r2 = await client.post('/login', data={'username': 'testuser', 'password': 'testpass'})
        print("STATUS FORM:", r2.status_code)
        print("BODY FORM:", r2.text)

if __name__ == '__main__':
    asyncio.run(test())
