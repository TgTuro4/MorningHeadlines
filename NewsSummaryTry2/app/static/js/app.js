// Global variables
let map;
let userLocation = null;
let locationDetails = null;

// Initialize Google Map
function initMap() {
    // Default location (will be updated when user location is detected)
    const defaultLocation = { lat: 40.7128, lng: -74.0060 }; // New York
    
    // Create the map
    map = new google.maps.Map(document.getElementById("map"), {
        zoom: 10,
        center: defaultLocation,
        mapId: "DEMO_MAP_ID",
        disableDefaultUI: true,
        zoomControl: true,
    });
    
    // Get user's location
    getUserLocation();
    
    // Add refresh button event listener
    document.getElementById("refresh-btn").addEventListener("click", refreshNews);
}

// Get user's geolocation
function getUserLocation() {
    // Show loading state
    document.getElementById("detected-location").textContent = "Detecting your location...";
    document.getElementById("loading").style.display = "flex";
    document.getElementById("news-container").innerHTML = "";
    document.getElementById("error-message").style.display = "none";
    
    // Check if geolocation is supported
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            // Success callback
            (position) => {
                userLocation = {
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude
                };
                
                // Update map with user location
                const latLng = { lat: userLocation.latitude, lng: userLocation.longitude };
                map.setCenter(latLng);
                
                // Add marker for user location
                new google.maps.Marker({
                    position: latLng,
                    map: map,
                    title: "Your Location",
                    animation: google.maps.Animation.DROP
                });
                
                // Get location details from coordinates
                getLocationDetails(userLocation);
            },
            // Error callback
            (error) => {
                handleError(`Geolocation error: ${error.message}. Please allow location access.`);
            }
        );
    } else {
        handleError("Geolocation is not supported by your browser.");
    }
}

// Get location details from coordinates using our backend API
async function getLocationDetails(coordinates) {
    try {
        const response = await fetch("/api/location", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(coordinates)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || "Failed to get location details");
        }
        
        locationDetails = await response.json();
        
        // Update UI with location info
        updateLocationUI(locationDetails);
        
        // Fetch news for this location
        fetchNews(locationDetails);
    } catch (error) {
        handleError(`Error getting location details: ${error.message}`);
    }
}

// Update UI with location information
function updateLocationUI(location) {
    let locationText = "Unknown location";
    
    if (location.city) {
        locationText = location.city;
        if (location.region) {
            locationText += `, ${location.region}`;
        }
        if (location.country && location.country !== location.region) {
            locationText += `, ${location.country}`;
        }
    } else if (location.formatted_address) {
        locationText = location.formatted_address;
    }
    
    document.getElementById("detected-location").textContent = locationText;
}

// Fetch news articles for the location
async function fetchNews(location) {
    try {
        const response = await fetch("/api/news", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ location })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || "Failed to fetch news");
        }
        
        const data = await response.json();
        
        // Display news articles
        displayNews(data.articles);
        
        // Display search queries
        displaySearchQueries(data.search_queries);
    } catch (error) {
        handleError(`Error fetching news: ${error.message}`);
    }
}

// Display news articles in the UI
function displayNews(articles) {
    const newsContainer = document.getElementById("news-container");
    const loading = document.getElementById("loading");
    
    // Hide loading indicator
    loading.style.display = "none";
    
    // Clear previous news
    newsContainer.innerHTML = "";
    
    // Check if we have articles
    if (!articles || articles.length === 0) {
        handleError("No news articles found for your location.");
        return;
    }
    
    // Get the template
    const template = document.getElementById("news-card-template");
    
    // Create and append news cards
    articles.forEach(article => {
        // Clone the template
        const newsCard = document.importNode(template.content, true);
        
        // Set image
        const imageElement = newsCard.querySelector(".news-image img");
        if (article.urlToImage) {
            imageElement.src = article.urlToImage;
            imageElement.alt = article.title;
        } else {
            imageElement.src = "/static/images/news-placeholder.jpg";
            imageElement.alt = "News placeholder image";
        }
        
        // Set title
        newsCard.querySelector(".news-title").textContent = article.title;
        
        // Set summary
        newsCard.querySelector(".news-summary").textContent = article.summary;
        
        // Set source
        newsCard.querySelector(".news-source").textContent = article.source;
        
        // Set link
        const readMoreLink = newsCard.querySelector(".read-more");
        readMoreLink.href = article.url;
        
        // Append to container
        newsContainer.appendChild(newsCard);
    });
}

// Handle errors
function handleError(message) {
    const errorElement = document.getElementById("error-message");
    const loading = document.getElementById("loading");
    
    // Hide loading indicator
    loading.style.display = "none";
    
    // Show error message
    errorElement.textContent = message;
    errorElement.style.display = "block";
}

// Refresh news
function refreshNews() {
    if (locationDetails) {
        document.getElementById("loading").style.display = "flex";
        document.getElementById("news-container").innerHTML = "";
        document.getElementById("error-message").style.display = "none";
        
        fetchNews(locationDetails);
    } else {
        getUserLocation();
    }
}

// Display search queries in the UI
function displaySearchQueries(queries) {
    if (!queries) {
        document.getElementById("search-queries").textContent = "No search query information available.";
        return;
    }
    
    const searchQueriesElement = document.getElementById("search-queries");
    searchQueriesElement.innerHTML = "";
    
    // Create a formatted display of the search queries
    const queryList = document.createElement("ul");
    queryList.className = "search-query-list";
    
    // Add endpoint information
    const endpointItem = document.createElement("li");
    endpointItem.innerHTML = `<strong>API Endpoint Used:</strong> ${queries.used_endpoint || "Unknown"}`;
    queryList.appendChild(endpointItem);
    
    // Add query terms based on which endpoint was used
    if (queries.used_endpoint === "top-headlines") {
        const queryItem = document.createElement("li");
        queryItem.innerHTML = `<strong>Search Term:</strong> ${queries.headlines_query || "None"}`;
        queryList.appendChild(queryItem);
        
        if (queries.country_code && queries.country_code !== "N/A") {
            const countryItem = document.createElement("li");
            countryItem.innerHTML = `<strong>Country Code:</strong> ${queries.country_code}`;
            queryList.appendChild(countryItem);
        }
    } else if (queries.used_endpoint === "everything") {
        const queryItem = document.createElement("li");
        queryItem.innerHTML = `<strong>Search Term:</strong> ${queries.everything_query || "None"}`;
        queryList.appendChild(queryItem);
        
        const languageItem = document.createElement("li");
        languageItem.innerHTML = `<strong>Language:</strong> ${queries.language || "Not specified"}`;
        queryList.appendChild(languageItem);
        
        const dateItem = document.createElement("li");
        dateItem.innerHTML = `<strong>From Date:</strong> ${queries.from_date || "Not specified"}`;
        queryList.appendChild(dateItem);
    } else if (queries.used_endpoint && queries.used_endpoint.includes("mock")) {
        // For mock data, show whatever queries we have
        if (queries.headlines_query) {
            const headlinesItem = document.createElement("li");
            headlinesItem.innerHTML = `<strong>Headlines Query:</strong> ${queries.headlines_query}`;
            queryList.appendChild(headlinesItem);
        }
        
        if (queries.everything_query) {
            const everythingItem = document.createElement("li");
            everythingItem.innerHTML = `<strong>Everything Query:</strong> ${queries.everything_query}`;
            queryList.appendChild(everythingItem);
        }
        
        if (queries.error) {
            const errorItem = document.createElement("li");
            errorItem.innerHTML = `<strong>Error:</strong> ${queries.error}`;
            errorItem.className = "error-item";
            queryList.appendChild(errorItem);
        }
    }
    
    searchQueriesElement.appendChild(queryList);
}

// Handle errors that might occur before the page is fully loaded
window.addEventListener("error", (event) => {
    console.error("Error:", event.error);
    handleError("An error occurred while loading the page. Please try refreshing.");
});
