import streamlit as st
import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_api_data(url):
    """
    Fetch and parse JSON data from API with proper error handling
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError if the status is 4xx, 5xx
        
        if response.text:  # Check if response body is not empty
            try:
                return response.json()
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode JSON: {e}")
                st.error("Failed to parse API response. Please check the API endpoint.")
                return None
        else:
            logger.warning("Empty response received from API")
            st.warning("Received empty response from API")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        st.error(f"Failed to fetch data: {str(e)}")
        return None

def main():
    st.title("Your App Title")
    
    # Your API endpoint
    API_URL = "YOUR_API_ENDPOINT_HERE"
    
    # Fetch data with error handling
    data = get_api_data(API_URL)
    
    if data is not None:
        # Process your data here
        st.write("Data fetched successfully:", data)
        # Add your data processing and visualization logic here
    else:
        st.write("Please check the API configuration and try again.")

if __name__ == "__main__":
    main()