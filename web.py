import os
from uvicorn.config import Config
import multiprocessing
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates

working_directory = os.path.dirname(os.path.abspath(__file__))
os.chdir(working_directory)

app = FastAPI()

# Mounting the static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


def read_log_file():
    file_path = "./config/auto_symlink.log"
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        return content
    except FileNotFoundError:
        return f"File not found:{file_path}."


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/get_log", response_class=PlainTextResponse)
async def get_log():
    return read_log_file()


if __name__ == "__main__":
    import uvicorn

    # Run the application using uvicorn
    Server = uvicorn.Server(
        Config(
            app,
            host="0.0.0.0",
            port=8095,
            reload=False,
            workers=multiprocessing.cpu_count(),
        )
    )
    # 启动服务
    Server.run()
