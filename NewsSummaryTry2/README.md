# Local News Summarizer

A FastAPI web application that shows summarized, location-based news to users in a clean, friendly format.

## Features

- **Location Detection**: Automatically detects user's location using browser geolocation
- **Local News**: Fetches relevant news articles based on the user's location
- **AI Summaries**: Summarizes news articles using OpenAI's ChatGPT
- **Interactive Map**: Displays the user's location on a Google Map
- **Responsive Design**: Clean, modern UI that works on all devices

## Technologies Used

- **Backend**: Python with FastAPI
- **Frontend**: HTML, CSS, JavaScript
- **APIs**:
  - Google Maps JavaScript + Geocoding API
  - NewsAPI.org
  - OpenAI ChatCompletion API

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- API keys for:
  - Google Maps API (with JavaScript and Geocoding enabled)
  - NewsAPI.org
  - OpenAI

### Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd LocalNewsSummarizer
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root and add your API keys:
   ```
   GOOGLE_API_KEY=your_google_api_key
   NEWSAPI_KEY=your_newsapi_key
   OPENAI_API_KEY=your_openai_api_key
   ```

### Running the Application

1. Start the application:
   ```
   uvicorn app.main:app --reload
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:8000
   ```

3. Allow location access when prompted by your browser to get local news.

## Project Structure

```
.
├── app
│   ├── main.py              # FastAPI application entry point
│   ├── routes               # API routes
│   │   └── news_routes.py   # News and location endpoints
│   ├── services             # External API integrations
│   │   ├── geocoding_service.py  # Google Maps Geocoding
│   │   ├── news_service.py       # NewsAPI
│   │   └── openai_service.py     # OpenAI
│   ├── static               # Static files
│   │   ├── css
│   │   │   └── styles.css   # Application styles
│   │   ├── js
│   │   │   └── app.js       # Frontend JavaScript
│   │   └── images           # Image assets
│   ├── templates            # Jinja2 templates
│   │   └── index.html       # Main page template
│   └── utils                # Utility functions
│       └── cache_utils.py   # Summary caching
├── .env                     # Environment variables (API keys)
└── requirements.txt         # Python dependencies
```

## Notes

- Summaries are cached to minimize OpenAI API calls
- Refresh button allows users to fetch the latest news
- Error handling is implemented for all API calls
