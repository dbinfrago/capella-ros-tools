# Copyright DB InfraGO AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""FastAPI app for viewing current snapshot of a Capella model."""

import typing as t
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

PATH = Path(__file__).parent


app = FastAPI(title="Capella ROS Tools")
app.mount(
    "/static", StaticFiles(directory=PATH.joinpath("static")), name="static"
)
templates = Jinja2Templates(directory=PATH.joinpath("templates"))


def get_type(xtype: str) -> str:
    """Return type name from xtype."""
    return xtype.rpartition(":")[2]


templates.env.globals.update(get_type=get_type)


@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    """Display root data package."""
    element = app.state.data_package
    context = {
        "request": request,
        "element": element,
        "get_type": get_type,
    }
    response = templates.TemplateResponse("package.html", context)
    return response


@app.get("/{type}/{uuid}", response_class=HTMLResponse)
def view(request: Request, type: str, uuid: str):
    """Display element by uuid."""
    element = app.state.model.by_uuid(uuid)
    template = type + ".html"

    context = {
        "request": request,
        "element": element,
        "get_type": get_type,
    }
    response = templates.TemplateResponse(template, context)
    return response


def start(model: t.Any, layer: str, port: int = 5000):
    """Start the app.""" ""
    app.state.model = model
    app.state.data_package = getattr(model, layer).data_package
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
    )
