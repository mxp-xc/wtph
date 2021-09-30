# -*- coding: utf-8 -*-
# @Time: 2021/9/30 17:05
from sanic import Sanic
from sanic.request import Request
from sanic.response import json

from wtph import setup_wtph

app = Sanic("My Hello, world app")
setup_wtph("sanic", app=app)


@app.get('/')
async def test(request):
    return json({'hello': 'world'})


if __name__ == '__main__':
    app.run()
