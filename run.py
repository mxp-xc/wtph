# -*- coding: utf-8 -*-
# @Time: 2021/8/15 17:27

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import wtph
from wtph import api, Query, get_openapi, get_swagger_ui_html

wtph.setup_wtph("flask")

app = FastAPI()


@api("/home_page", methods=['GET'])
@app.get("/home_page")
async def index(
        a: int = Query(..., ge=100, alias="p1"),
        b: str = Query(...)
):
    return locals()


@app.get("/openapi")
async def get_openapi_json():
    return get_openapi(
        title="test",
        version="0.1",
    )


@app.get("/my_docs")
async def get_docs():
    return HTMLResponse(get_swagger_ui_html(
        openapi_url="/openapi",
        title="test",
    ))


if __name__ == '__main__':
    import uvicorn

    uvicorn.run("run:app")
