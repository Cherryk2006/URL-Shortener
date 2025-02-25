import json
import os.path
import string
import random
from typing import Annotated

from fastapi import FastAPI, Request, Form, HTTPException
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates

PATH_TO_DATA_FILE = "links.json"

app = FastAPI()

templates = Jinja2Templates(directory="templates")

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.post("/")
async def get_short_url(request: Request, long_url: Annotated[str, Form()]):
    short_url = "".join(
        [random.choice(string.ascii_letters + string.digits) for _ in range(8)]
    )

    if not os.path.isfile(PATH_TO_DATA_FILE):
        with open(PATH_TO_DATA_FILE, "w") as file:
            file.write(json.dumps({short_url: long_url}))
    else:
        with open(PATH_TO_DATA_FILE, "r") as file:
            data = json.loads(file.read())
        with open(PATH_TO_DATA_FILE, "w") as file:
            data[short_url] = long_url
            file.write(json.dumps(data))

    return templates.TemplateResponse(request=request, name="show_url_page.html", context={"short_url": short_url})

@app.get("/urls")
async def get_urls(request: Request):
    if not os.path.isfile(PATH_TO_DATA_FILE):
        with open(PATH_TO_DATA_FILE, "w") as file:
            file.write(json.dumps({}))
    with open(PATH_TO_DATA_FILE, "r") as file:
        data = json.loads(file.read())

    return templates.TemplateResponse(request=request, name="urls_list.html", context={"urls": data})

@app.get("/{short_url}")
async def redirect_short_url(request: Request, short_url: str):
    if not os.path.isfile(PATH_TO_DATA_FILE):
        with open(PATH_TO_DATA_FILE, "w") as file:
            file.write(json.dumps({}))
    with open(PATH_TO_DATA_FILE, "r") as file:
        redirect = json.loads(file.read()).get(short_url)
    if redirect is None:
        raise HTTPException(status_code=404, detail="URL not found")
    return RedirectResponse(url=redirect)