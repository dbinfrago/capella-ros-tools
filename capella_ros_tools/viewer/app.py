# Copyright DB InfraGO AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Web view of Capella data package."""

import pathlib
import typing as t

import fastapi
import uvicorn
from fastapi import responses, staticfiles, templating

PATH = pathlib.Path(__file__).parent


app = fastapi.FastAPI(title="Capella JSON Tools")
app.mount(
    "/static",
    staticfiles.StaticFiles(directory=PATH.joinpath("static")),
    name="static",
)
templates = templating.Jinja2Templates(directory=PATH.joinpath("templates"))


def get_type(xtype: str) -> str:
    """Return type name from xtype."""
    return xtype.rpartition(":")[2]


templates.env.globals.update(get_type=get_type)


@app.get("/", response_class=responses.HTMLResponse)
def root(request: fastapi.Request):
    """Display root data package."""
    element = app.state.data_package
    context = {
        "request": request,
        "element": element,
        "get_type": get_type,
    }
    response = templates.TemplateResponse("package.html", context)
    return response


@app.get("/{type}/{uuid}.html", response_class=responses.HTMLResponse)
def view(request: fastapi.Request, type: str, uuid: str):
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
