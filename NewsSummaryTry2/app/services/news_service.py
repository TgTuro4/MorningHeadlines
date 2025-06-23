import os
import requests
import datetime
import json
import hashlib
from openai import OpenAI
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
        # Initialize OpenAI client
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # Initialize summary cache
        self.summary_cache = {}
        
    async def get_local_news(self, location):
        """
        Fetch local news based on location information and ensure articles are relevant to the location
        
        Args:
            location (dict): Location information containing city, region, country, etc.
            
        Returns:
            list: List of news articles relevant to the location
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
                    articles = data.get("articles", [])
                    article_count = len(articles)
                    print(f"Found {article_count} headline articles")
                    
                    # Check if we have at least 10 articles
                    if article_count >= 10:
                        processed_articles = self._process_articles(articles, location)
                        # Store the search queries used
                        self.last_search_queries = {
                            "headlines_query": headlines_params.get("q", "N/A"),
                            "country_code": headlines_params.get("country", "N/A"),
                            "used_endpoint": "top-headlines",
                            "article_count": article_count
                        }
                        return processed_articles
                    else:
                        print(f"Top-headlines returned only {article_count} articles, which is less than 10. Falling back to everything endpoint.")
                        # Continue to everything endpoint
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
                        articles = self._process_articles(data.get("articles", []), location)
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

    def _process_articles(self, articles, location=None):
        processed_articles = []
        # First process all articles to have a larger pool to filter from
        for article in articles[:20]:  # Process more articles initially to account for filtering
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
        
        # If location is provided, vet articles for relevance
        if location:
            return self._vet_articles_for_location(processed_articles, location)
        
        # Otherwise just return the first 16 articles
        return processed_articles[:16]
        
    def get_search_queries(self):
        """
        Return the search queries that were used in the last API call
        """
        return self.last_search_queries
        
    def _generate_article_hash(self, article):
        """
        Generate a unique hash for an article based on its URL and title
        
        Args:
            article (dict): The article to generate a hash for
            
        Returns:
            str: A unique hash for the article
        """
        # Use URL as primary identifier since it should be unique
        url = article.get('url', '')
        # Add title as backup in case URL is missing
        title = article.get('title', '')
        # Generate hash
        hash_input = f"{url}|{title}"
        return hashlib.md5(hash_input.encode('utf-8')).hexdigest()
    
    def _get_cached_summary(self, article_hash):
        """
        Get a cached summary for an article if it exists
        
        Args:
            article_hash (str): The hash of the article
            
        Returns:
            str: The cached summary or None if not found
        """
        return self.summary_cache.get(article_hash)
    
    def _cache_summary(self, article_hash, summary):
        """
        Cache a summary for an article
        
        Args:
            article_hash (str): The hash of the article
            summary (str): The summary to cache
        """
        self.summary_cache[article_hash] = summary
        
        # Keep cache size reasonable (limit to 1000 entries)
        if len(self.summary_cache) > 1000:
            # Remove oldest entries (simple approach: just remove some random entries)
            keys_to_remove = list(self.summary_cache.keys())[:100]
            for key in keys_to_remove:
                del self.summary_cache[key]
    
    def _check_relevance_for_cached_article(self, cached_summary, target_region):
        """
        Check if a cached article summary is relevant to the target region
        
        Args:
            cached_summary (str): The cached summary of the article
            target_region (str): The target region to check relevance for
            
        Returns:
            dict: A result object with relevance information
        """
        prompt = f"""Given this summary of a news article, determine if the state/region '{target_region}' is EXPLICITLY mentioned or DIRECTLY relevant.
        
        Summary: {cached_summary}
        
        Apply STRICT criteria for relevance:
        - The summary must EXPLICITLY mention '{target_region}' by name OR
        - The summary must discuss events, policies, or issues that DIRECTLY and SPECIFICALLY impact '{target_region}'
        
        Respond with a JSON object with this format: {{
            "mentions_region": true|false,
            "relevance_score": 0-10 (where 0 means completely irrelevant and 10 means directly about this region),
            "justification": "Brief explanation of why this article is or is not relevant to the region"
        }}
        """
        
        try:
            # This API call is much smaller since we're only sending the summary
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            result = json.loads(response.choices[0].message.content)
            # Add the cached summary to the result
            result["summary"] = cached_summary
            return result
            
        except Exception as e:
            print(f"Error checking relevance for cached article: {str(e)}")
            # Return a default result that will likely not pass the relevance check
            return {
                "summary": cached_summary,
                "mentions_region": False,
                "relevance_score": 0,
                "justification": "Error checking relevance for cached summary"
            }
        
    def _vet_articles_for_location(self, articles, location):
        """
        Use AI to summarize each article and check if the state/region is mentioned in the summary.
        Continue fetching articles until 10 slots are filled with relevant articles.
        
        Args:
            articles (list): List of processed articles
            location (dict): Location information containing city, region, country, etc.
            
        Returns:
            list: List of articles that are relevant to the location, limited to 16
        """
        if not articles:
            return []
            
        # Skip vetting if OpenAI API key is not available
        if not os.getenv("OPENAI_API_KEY"):
            print("OpenAI API key not found, skipping article vetting")
            return articles[:16]
            
        try:
            # Get the state/region we're looking for
            target_region = location.get("region", "")
            if not target_region:
                print("No region/state information available for vetting")
                return articles[:16]
                
            print(f"Vetting articles for relevance to state/region: {target_region}")
            
            # Process articles one by one until we have 10 relevant ones
            relevant_articles = []
            articles_to_process = list(articles)  # Create a copy to avoid modifying the original
            processed_count = 0
            
            while len(relevant_articles) < 10 and processed_count < len(articles_to_process):
                try:
                    article = articles_to_process[processed_count]
                    processed_count += 1
                    
                    # Extract article content for summarization
                    article_content = f"Title: {article.get('title', '')}"
                    if article.get('description'):
                        article_content += f"\nDescription: {article.get('description')}"
                    if article.get('content'):
                        article_content += f"\nContent: {article.get('content')}"
                    
                    # Generate a unique hash for this article to use as cache key
                    article_hash = self._generate_article_hash(article)
                    
                    # Check if we have a cached summary for this article
                    cached_summary = self._get_cached_summary(article_hash)
                    
                    if cached_summary:
                        print(f"Using cached summary for article: {article.get('title', '')[:40]}...")
                        # We still need to check relevance for this specific region
                        result = self._check_relevance_for_cached_article(cached_summary, target_region)
                    else:
                        # Create a prompt for the AI to summarize and check relevance
                        prompt = f"""Summarize the following news article in 2-3 sentences. Then determine if the state/region '{target_region}' is EXPLICITLY mentioned or DIRECTLY relevant to the article content.
                        
                        Article:
                        {article_content}
                        
                        Apply STRICT criteria for relevance:
                        - The article must EXPLICITLY mention '{target_region}' by name OR
                        - The article must discuss events, policies, or issues that DIRECTLY and SPECIFICALLY impact '{target_region}' (not just general news that might affect many regions)
                        - Articles about nearby regions or general national news should NOT be considered relevant unless they specifically discuss impacts on '{target_region}'
                        
                        Respond with a JSON object with this format: {{
                            "summary": "Your 2-3 sentence summary here",
                            "mentions_region": true|false,
                            "relevance_score": 0-10 (where 0 means completely irrelevant and 10 means directly about this region),
                            "justification": "Brief explanation of why this article is or is not relevant to the region"
                        }}
                        """
                        
                        try:
                            # Call the OpenAI API for this specific article
                            response = self.openai_client.chat.completions.create(
                                model="gpt-3.5-turbo",
                                messages=[{"role": "system", "content": prompt}],
                                temperature=0.1,
                                response_format={"type": "json_object"}
                            )
                            
                            # Parse the response
                            result = json.loads(response.choices[0].message.content)
                            
                            # Cache the summary
                            if "summary" in result:
                                self._cache_summary(article_hash, result["summary"])
                        except Exception as e:
                            print(f"Error summarizing article: {str(e)}")
                            result = {
                                "summary": "Error generating summary",
                                "mentions_region": False,
                                "relevance_score": 0,
                                "justification": "Error processing article"
                            }
                            
                    # Add the summary to the article
                    article["ai_summary"] = result.get("summary", "No summary available")
                    
                    # Check if the article mentions or is relevant to the region - using stricter criteria
                    mentions_region = result.get("mentions_region", False)
                    relevance_score = result.get("relevance_score", 0)
                    justification = result.get("justification", "No justification provided")
                    
                    # Store the AI analysis in the article object
                    article["ai_analysis"] = {
                        "mentions_region": mentions_region,
                        "relevance_score": relevance_score,
                        "justification": justification
                    }
                    
                    # Stricter criteria: Must explicitly mention region AND have a high relevance score
                    if mentions_region and relevance_score >= 7:
                        print(f"Article HIGHLY relevant to {target_region} (score: {relevance_score}): {article.get('title')}")
                        print(f"Justification: {justification}")
                        relevant_articles.append(article)
                    else:
                        print(f"Article NOT sufficiently relevant to {target_region} (score: {relevance_score}): {article.get('title')}")
                        print(f"Justification: {justification}")
                except Exception as article_error:
                    print(f"Error processing article: {str(article_error)}")
                    # If there's an error, we'll consider the article not relevant
            
            print(f"Found {len(relevant_articles)} articles relevant to {target_region} after processing {processed_count} articles")
            
            # If we don't have enough relevant articles, try with slightly less strict criteria
            if len(relevant_articles) < 5 and processed_count >= len(articles_to_process):
                print(f"Very few highly relevant articles found, applying less strict criteria for a second pass")
                
                # Second pass with less strict criteria
                for article in articles_to_process:
                    if article in relevant_articles:
                        continue  # Skip articles already deemed relevant
                        
                    # Check if the article has AI analysis
                    if "ai_analysis" in article:
                        # Less strict criteria for second pass
                        if (article["ai_analysis"].get("mentions_region", False) or 
                            article["ai_analysis"].get("relevance_score", 0) >= 5):
                            print(f"Adding article with moderate relevance to {target_region}: {article.get('title')}")
                            relevant_articles.append(article)
                            if len(relevant_articles) >= 10:
                                break
            
            # If we still don't have enough relevant articles, supplement with the remaining articles
            if len(relevant_articles) < 10:
                print(f"Not enough relevant articles found, supplementing with non-region specific articles")
                remaining_articles = [a for a in articles_to_process if a not in relevant_articles]
                return (relevant_articles + remaining_articles)[:16]
            else:
                return relevant_articles[:16]
                
        except Exception as e:
            print(f"Error during article vetting: {str(e)}")
            return articles[:16]
