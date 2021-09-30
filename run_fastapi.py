# -*- coding: utf-8 -*-
# @Time: 2021/9/21 14:29
from fastapi import FastAPI, Query, Form
from pydantic import BaseModel

app = FastAPI()


class PageModel(BaseModel):
    page: int = Query(1, ge=1)
    page_size: int = Query(20, ge=1, le=50)


def depend(
        b: PageModel
):
    return b


@app.post("/")
async def index(
        c: str,
        a: int = Form(...),
):
    pass


if __name__ == '__main__':
    import uvicorn

    uvicorn.run("run_fastapi:app")
