import string
import random
import motor.motor_asyncio
from typing import Annotated

from fastapi import FastAPI, Request, Form, HTTPException
from starlette import status
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates
app = FastAPI()

db_client = motor.motor_asyncio.AsyncIOMotorClient("localhost", 27017)

app_db = db_client.url_shortener

collection = app_db.urls

templates = Jinja2Templates(directory="templates")

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.post("/")
async def get_short_url(request: Request, long_url: Annotated[str, Form()]):
    short_url = "".join(
        [random.choice(string.ascii_letters + string.digits) for _ in range(8)]
    )
    await collection.insert_one({"short_url": short_url, "long_url": long_url, "clicks": 0})
    return templates.TemplateResponse(request=request, name="show_url_page.html", context={"short_url": short_url})

@app.get("/urls")
async def get_urls(request: Request):
    data = await collection.find().to_list()

    return templates.TemplateResponse(request=request, name="urls_list.html", context={"urls": data})

@app.get("/{short_url}")
async def redirect_short_url(request: Request, short_url: str):
    collection_data = await collection.find_one({"short_url": short_url})
    redirect = collection_data.get("long_url") if collection_data else None

    if redirect is None:
        raise HTTPException(status_code=404, detail="URL not found")

    await collection.update_one({"short_url": short_url}, {"$inc": {"clicks": 1}})

    return RedirectResponse(url=redirect)

@app.get("/{short_url}/edit")
async def get_edit_url_page(request: Request, short_url: str):
    collection_data = await collection.find_one({"short_url": short_url})
    redirect = collection_data.get("long_url") if collection_data else None

    if redirect is None:
        raise HTTPException(status_code=404, detail="URL not found")

    return templates.TemplateResponse(request=request, name="edit_page.html", context={"short_url": short_url, "long_url": redirect})

@app.post("/{short_url}/edit")
async def edit_long_url(request: Request, short_url: str, long_url: Annotated[str, Form()]):
    collection_data = await collection.find_one({"short_url": short_url})

    if collection_data:
        collection.update_one({"short_url": short_url}, {"$set": {"long_url": long_url}})

    redirect_url = request.url_for("get_urls")
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)

@app.post("/{short_url}/delete")
async def delete_short_url(request: Request, short_url: str):
    collection_data = await collection.find_one({"short_url": short_url})
    if collection_data:
        await collection.delete_one({"short_url": short_url})

    redirect_url = request.url_for("get_urls")
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)