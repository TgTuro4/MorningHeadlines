// Global variables
let map;
let userLocation = null;
let locationDetails = null;
let geocoder = null;
let searchHistory = [];

// Load search history from localStorage if available
function loadSearchHistory() {
    const savedHistory = localStorage.getItem('searchHistory');
    if (savedHistory) {
        try {
            searchHistory = JSON.parse(savedHistory);
        } catch (e) {
            console.error('Error loading search history:', e);
            searchHistory = [];
        }
    } else {
        searchHistory = [];
    }
    
    // Initialize the search history UI
    updateSearchHistoryUI();
}

// Save search history to localStorage
function saveSearchHistory() {
    try {
        localStorage.setItem('searchHistory', JSON.stringify(searchHistory));
    } catch (e) {
        console.error('Error saving search history:', e);
    }
}

// Add a search to history
function addToSearchHistory(address, lat, lng) {
    // Don't add duplicates
    const existingIndex = searchHistory.findIndex(item => 
        item.address.toLowerCase() === address.toLowerCase());
    
    if (existingIndex !== -1) {
        // Move to top if exists
        const item = searchHistory.splice(existingIndex, 1)[0];
        searchHistory.unshift(item);
    } else {
        // Add new entry
        searchHistory.unshift({
            address: address,
            latitude: lat,
            longitude: lng,
            timestamp: new Date().toISOString()
        });
        
        // Keep only the last 5 searches
        if (searchHistory.length > 5) {
            searchHistory.pop();
        }
    }
    
    saveSearchHistory();
    updateSearchHistoryUI();
}

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
    
    // Initialize geocoder
    geocoder = new google.maps.Geocoder();
    
    // Load search history
    loadSearchHistory();
    
    // Get user's location
    getUserLocation();
    
    // Add event listeners
    document.getElementById("refresh-btn").addEventListener("click", refreshNews);
    document.getElementById("manual-location-btn").addEventListener("click", showManualLocationForm);
    document.getElementById("search-address-btn").addEventListener("click", searchManualAddress);
    document.getElementById("cancel-address-btn").addEventListener("click", hideManualLocationForm);
    document.getElementById("address-input").addEventListener("keypress", function(event) {
        if (event.key === "Enter") {
            searchManualAddress();
        }
    });
    
    // Initialize search history UI
    updateSearchHistoryUI();
    
    // Hide manual location form by default
    hideManualLocationForm();
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
                
                // Add marker for user location using AdvancedMarkerElement
                const markerView = new google.maps.marker.AdvancedMarkerElement({
                    position: latLng,
                    map: map,
                    title: "Your Location"
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
    const errorElement = document.getElementById("error-message");
    
    // Hide loading and error
    loading.style.display = "none";
    errorElement.style.display = "none";
    
    // Clear previous news
    newsContainer.innerHTML = "";
    
    if (!articles || articles.length === 0) {
        errorElement.textContent = "No news articles found for your location.";
        errorElement.style.display = "block";
        return;
    }
    
    // Get the template
    const template = document.getElementById("news-card-template");
    
    // Create and append news cards with staggered animation
    articles.forEach((article, index) => {
        // Clone the template
        const newsCard = document.importNode(template.content, true);
        
        // Set the content
        const image = newsCard.querySelector(".news-image img");
        const title = newsCard.querySelector(".news-title");
        const summary = newsCard.querySelector(".news-summary");
        const source = newsCard.querySelector(".news-source");
        const readMore = newsCard.querySelector(".read-more");
        
        // Set animation order for staggered effect
        const card = newsCard.querySelector(".news-card");
        card.style.setProperty('--animation-order', index);
        
        // Set image with fallback
        if (article.urlToImage) {
            image.src = article.urlToImage;
            image.alt = article.title;
        } else {
            image.src = "/static/img/news-placeholder.jpg";
            image.alt = "News placeholder image";
        }
        
        // Handle image loading errors
        image.onerror = function() {
            this.src = "/static/img/news-placeholder.jpg";
            this.alt = "News placeholder image";
        };
        
        title.textContent = article.title;
        summary.textContent = article.summary;
        source.textContent = article.source;
        readMore.href = article.url;
        
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

// Refresh news with animation
function refreshNews() {
    if (locationDetails) {
        // Add animation class to refresh button
        const refreshBtn = document.getElementById("refresh-btn");
        refreshBtn.classList.add("refreshing");
        refreshBtn.disabled = true;
        
        // Create refresh animation
        const newsContainer = document.getElementById("news-container");
        const cards = newsContainer.querySelectorAll('.news-card');
        
        // Animate cards out
        cards.forEach((card, index) => {
            setTimeout(() => {
                card.style.opacity = "0";
                card.style.transform = "translateY(30px)";
            }, index * 50);
        });
        
        // After animation completes, show loading and fetch new news
        setTimeout(() => {
            document.getElementById("loading").style.display = "flex";
            document.getElementById("news-container").innerHTML = "";
            document.getElementById("error-message").style.display = "none";
            
            fetchNews(locationDetails);
            
            // Reset refresh button after a delay
            setTimeout(() => {
                refreshBtn.classList.remove("refreshing");
                refreshBtn.disabled = false;
            }, 1000);
        }, cards.length ? cards.length * 50 + 300 : 0);
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

// Update search history UI
function updateSearchHistoryUI() {
    const historyList = document.getElementById('history-list');
    historyList.innerHTML = '';
    
    if (searchHistory.length > 0) {
        searchHistory.forEach((item, index) => {
            const li = document.createElement('li');
            li.className = 'history-item';
            
            // Format the address (truncate if too long)
            let displayAddress = item.address;
            if (displayAddress.length > 30) {
                displayAddress = displayAddress.substring(0, 27) + '...';
            }
            
            li.textContent = displayAddress;
            
            // Add click handler
            li.addEventListener('click', () => {
                useHistoryLocation(item);
            });
            
            historyList.appendChild(li);
        });
        
        // Show history section when we have items
        const historySection = document.getElementById('search-history');
        historySection.style.display = 'block';
    } else {
        // If no history, show a message
        const li = document.createElement('li');
        li.className = 'history-item no-history';
        li.textContent = 'No search history yet';
        historyList.appendChild(li);
        
        // Always show the history section
        const historySection = document.getElementById('search-history');
        historySection.style.display = 'block';
    }
}

// Use a location from history
function useHistoryLocation(historyItem) {
    document.getElementById("detected-location").textContent = "Loading location...";
    document.getElementById("loading").style.display = "flex";
    
    // Update map
    const location = { lat: historyItem.latitude, lng: historyItem.longitude };
    map.setCenter(location);
    map.setZoom(10);
    
    // Create a marker
    const markerView = new google.maps.marker.AdvancedMarkerElement({
        position: location,
        map: map
    });
    
    // Get location details
    getLocationDetails({
        latitude: historyItem.latitude,
        longitude: historyItem.longitude
    });
    
    // Clear the address input
    clearAddressInput();
}

// Clear the address input
function clearAddressInput() {
    document.getElementById("address-input").value = "";
}

// Show manual location form
function showManualLocationForm() {
    document.getElementById("manual-location-form").style.display = "block";
    document.getElementById("address-input").focus();
}

// Hide manual location form
function hideManualLocationForm() {
    document.getElementById("manual-location-form").style.display = "none";
    clearAddressInput();
}

// Search for manually entered address
function searchManualAddress() {
    const address = document.getElementById("address-input").value.trim();
    
    if (!address) {
        alert("Please enter an address or location");
        return;
    }
    
    document.getElementById("detected-location").textContent = "Searching for location...";
    document.getElementById("loading").style.display = "flex";
    hideManualLocationForm();
    
    geocoder.geocode({ address: address }, function(results, status) {
        if (status === "OK" && results[0]) {
            const location = results[0].geometry.location;
            const lat = location.lat();
            const lng = location.lng();
            
            // Add to search history
            addToSearchHistory(address, lat, lng);
            
            // Update map
            map.setCenter(location);
            map.setZoom(10);
            
            // Create a marker
            const markerView = new google.maps.marker.AdvancedMarkerElement({
                position: location,
                map: map
            });
            
            // Get location details
            getLocationDetails({
                latitude: lat,
                longitude: lng
            });
            
            // Clear the address input
            clearAddressInput();
        } else {
            handleError("Could not find the specified location. Please try again.");
            clearAddressInput();
        }
    });
}

// Handle errors that might occur before the page is fully loaded
window.addEventListener("error", (event) => {
    console.error("Error:", event.error);
    handleError("An error occurred while loading the page. Please try refreshing.");
});
