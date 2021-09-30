# -*- coding: utf-8 -*-
# @Time: 2021/8/13 21:15
from flask import Flask
from wtph import Query, setup_wtph
from wtph.injects.flask import type_hint

app = type_hint(Flask(__name__))
setup_wtph("flask", app=app)


@app.get("/", view_config={"description": "描述123"})
def f(
        b: str = Query(...),
):
    return locals()


@app.get("/async")
async def f1(
):
    return locals()


if __name__ == '__main__':
    app.run()
