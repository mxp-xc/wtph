# -*- coding: utf-8 -*-
# @Time: 2021/9/30 17:05
from sanic import Sanic
from sanic.response import json

from wtph import setup_wtph, Query
from wtph.injects.sanic import type_hint

app = type_hint(Sanic("My Hello, world app"))
setup_wtph("sanic", app=app)


@app.get('/')
async def test(
        a: int = Query(...),
):
    return json(locals())


if __name__ == '__main__':
    app.run()
