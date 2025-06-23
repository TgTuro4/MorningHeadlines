import os
import requests
import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class NewsService:
    """
    Service for fetching news articles from NewsAPI.org
    """
    
    def __init__(self):
        self.api_key = os.getenv("NEWSAPI_KEY")
        self.base_url = "https://newsapi.org/v2"
        # Flag to indicate if we should use mock data
        self.use_mock = False
        # Track search queries
        self.last_search_queries = {}
        
    async def get_local_news(self, location):
        """
        Fetch local news based on location information
        
        Args:
            location (dict): Location information containing city, region, country, etc.
            
        Returns:
            list: List of news articles
        """
        # If we're in mock mode, return mock data
        if self.use_mock:
            print("Using mock news data")
            # Import mock_news only when needed to avoid circular imports
            from app.utils import mock_news
            return mock_news.get_mock_news(location)
            
        try:
            print(f"News service received location: {location}")
            
            # Determine the best query parameter based on available location info
            headlines_params = {}
            everything_params = {}
            
            # Set up query for both endpoints - prioritize region/state over city
            if location.get("region"):
                headlines_params["q"] = location["region"]
                everything_params["q"] = location["region"]
                print(f"Using region for query: {location['region']}")
            elif location.get("country"):
                headlines_params["q"] = location["country"]
                everything_params["q"] = location["country"]
                print(f"Using country for query: {location['country']}")
            else:
                # Default query
                headlines_params["q"] = "news"
                everything_params["q"] = "news"
                print("No location data available, using default query 'news'")
                
            # Store city information for reference, even though we're not using it as the primary query
            if location.get("city"):
                print(f"Note: City information available ({location['city']}) but using region/country instead")
                
            # Country code is only valid for top-headlines
            if location.get("country_code"):
                country_code = location["country_code"].lower()
                if len(country_code) == 2:
                    headlines_params["country"] = country_code
                    print(f"Using country code for headlines: {country_code}")
            
            # Add common parameters
            headlines_params["apiKey"] = self.api_key
            headlines_params["pageSize"] = 16
            
            everything_params["apiKey"] = self.api_key
            everything_params["pageSize"] = 16
            everything_params["language"] = "en"
            everything_params["sortBy"] = "publishedAt"
            
            # Add date parameter (required for some API plans)
            today = datetime.datetime.now()
            month_ago = today - datetime.timedelta(days=30)
            everything_params["from"] = month_ago.strftime("%Y-%m-%d")
            
            # Try top-headlines first (more relevant but limited coverage)
            print(f"Trying top-headlines with params: {headlines_params}")
            try:
                headlines_response = requests.get(f"{self.base_url}/top-headlines", params=headlines_params)
                print(f"Top-headlines response status: {headlines_response.status_code}")
                
                if headlines_response.status_code == 200:
                    data = headlines_response.json()
                    if data.get("totalResults", 0) > 0:
                        print(f"Found {len(data.get('articles', []))} headline articles")
                        articles = self._process_articles(data.get("articles", []))
                        # Store the search queries used
                        self.last_search_queries = {
                            "headlines_query": headlines_params.get("q", "N/A"),
                            "country_code": headlines_params.get("country", "N/A"),
                            "used_endpoint": "top-headlines"
                        }
                        return articles
            except Exception as headline_error:
                print(f"Error with headlines endpoint: {str(headline_error)}")
            
            # If headlines didn't work or returned no results, try everything endpoint
            print(f"Trying everything endpoint with params: {everything_params}")
            try:
                everything_response = requests.get(f"{self.base_url}/everything", params=everything_params)
                print(f"Everything response status: {everything_response.status_code}")
                
                if everything_response.status_code == 200:
                    data = everything_response.json()
                    if data.get("totalResults", 0) > 0:
                        print(f"Found {len(data.get('articles', []))} articles from everything endpoint")
                        articles = self._process_articles(data.get("articles", []))
                        # Store the search queries used
                        self.last_search_queries = {
                            "everything_query": everything_params.get("q", "N/A"),
                            "language": everything_params.get("language", "N/A"),
                            "from_date": everything_params.get("from", "N/A"),
                            "used_endpoint": "everything"
                        }
                        return articles
                    else:
                        print("No articles found in everything endpoint")
                else:
                    error_data = everything_response.json() if everything_response.content else {"message": "Unknown error"}
                    print(f"Everything endpoint error: {everything_response.status_code} - {error_data}")
            except Exception as everything_error:
                print(f"Error with everything endpoint: {str(everything_error)}")
            
            # If we got here, both endpoints failed or returned no results
            # Enable mock mode for future requests and return mock data this time
            print("API requests failed or returned no results. Switching to mock data.")
            self.use_mock = True
            # Import mock_news only when needed to avoid circular imports
            from app.utils import mock_news
            mock_data = mock_news.get_mock_news(location)
            self.last_search_queries = {
                "headlines_query": headlines_params.get("q", "N/A"),
                "everything_query": everything_params.get("q", "N/A"),
                "country_code": headlines_params.get("country", "N/A"),
                "used_endpoint": "mock_data"
            }
            return mock_data
            
        except Exception as e:
            print(f"Exception in news service: {str(e)}")
            # Fall back to mock data on any error
            self.use_mock = True
            # Import mock_news only when needed to avoid circular imports
            from app.utils import mock_news
            mock_data = mock_news.get_mock_news(location)
            self.last_search_queries = {
                "error": str(e),
                "used_endpoint": "mock_data (error fallback)"
            }
            return mock_data

    def _process_articles(self, articles):
        processed_articles = []
        for article in articles[:16]:  # Limit to 16 articles
            processed_article = {
                "title": article.get("title", ""),
                "description": article.get("description", ""),
                "content": article.get("content", ""),
                "url": article.get("url", ""),
                "urlToImage": article.get("urlToImage", ""),
                "source": article.get("source", {}).get("name", "Unknown Source"),
                "publishedAt": article.get("publishedAt", "")
            }
            processed_articles.append(processed_article)
        return processed_articles
        
    def get_search_queries(self):
        """
        Return the search queries that were used in the last API call
        """
        return self.last_search_queries
