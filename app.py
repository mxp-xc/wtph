# -*- coding: utf-8 -*-
# @Time: 2021/8/13 21:15
from flask import Flask
from wtph import Query, api, get_openapi, get_swagger_ui_html, Body, setup_wtph
from wtph.config import config
from wtph.parsers.flask import flask_parser_manager_factory

app = Flask(__name__)
setup_wtph("flask", app=app)


def f():
    return "1"


@app.get("/")
def f(
        b: str = Query(...),
):
    return locals()


if __name__ == '__main__':
    app.run()
