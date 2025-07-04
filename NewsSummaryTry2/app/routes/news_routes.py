from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from app.services.geocoding_service import GeocodingService
from app.services.news_service import NewsService
from app.services.openai_service import OpenAIService

router = APIRouter(prefix="/api")

# Initialize services
geocoding_service = GeocodingService()
news_service = NewsService()
openai_service = OpenAIService()

class LocationRequest(BaseModel):
    latitude: float
    longitude: float

@router.post("/location")
async def process_location(request: LocationRequest):
    """
    Process user location and return location details
    """
    try:
        location = await geocoding_service.get_location_from_coordinates(
            request.latitude, 
            request.longitude
        )
        
        if "error" in location:
            return JSONResponse(
                status_code=400,
                content={"error": location["error"]}
            )
            
        return location
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/news")
async def get_news(request: Dict[str, Any]):
    """
    Get news articles based on location
    """
    try:
        print(f"Received news request with data: {request}")
        location = request.get("location", {})
        if not location:
            print("Error: No location data provided in request")
            return JSONResponse(
                status_code=400,
                content={"error": "Location data is required"}
            )
            
        print(f"Fetching news for location: {location}")
        # Get news articles
        articles = await news_service.get_local_news(location)
        
        if isinstance(articles, dict) and "error" in articles:
            print(f"Error from news service: {articles['error']}")
            return JSONResponse(
                status_code=400,
                content={"error": articles["error"]}
            )
            
        # Get the search queries that were used
        search_queries = news_service.get_search_queries()
        print(f"Search queries used: {search_queries}")
            
        # Process and summarize articles
        processed_articles = []
        
        print(f"Processing {len(articles)} articles")
        for i, article in enumerate(articles):
            try:
                print(f"Summarizing article {i+1}/{len(articles)}: {article.get('title', 'No title')}")
                # Generate summary for each article
                summary = await openai_service.summarize_article(article)
                    
                # Add summary to article
                article["summary"] = summary
                processed_articles.append(article)
            except Exception as article_error:
                print(f"Error processing article {i+1}: {str(article_error)}")
                # Add a default summary if there's an error
                article["summary"] = "Summary unavailable."
                processed_articles.append(article)
            
        print(f"Successfully processed {len(processed_articles)} articles")
        return {"articles": processed_articles, "location": location, "search_queries": search_queries}
    except Exception as e:
        print(f"ERROR in /news endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": f"Server error: {str(e)}"}
        )
