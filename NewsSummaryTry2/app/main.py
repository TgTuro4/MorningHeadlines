from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import uvicorn
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="LocalNews Summarizer")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="app/templates")

# Import routes
from app.routes import news_routes

# Include routers
app.include_router(news_routes.router)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    Root endpoint that renders the main page
    """
    # Pass Google API key to the template
    google_api_key = os.getenv("GOOGLE_API_KEY")
    return templates.TemplateResponse("index.html", {"request": request, "google_api_key": google_api_key})

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
