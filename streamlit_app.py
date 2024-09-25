# Import necessary libraries
import streamlit as st
import pandas as pd
import re

# Function to extract TikTok usernames from a list of URLs
def extract_tiktok_usernames(urls):
    """
    This function takes a list of TikTok channel URLs, extracts the usernames,
    and provides feedback for any URLs that couldn't be processed.
    """
    # Regular expression to match valid TikTok URLs and extract username
    pattern = re.compile(r"(?:https?://)?(?:www\.)?tiktok\.com/@([A-Za-z0-9_.]+)")
    
    valid_usernames = []
    invalid_urls = []

    # Loop through each URL and attempt to extract the username
    for url in urls:
        match = pattern.match(url.strip())
        if match:
            # Add valid usernames to the list
            valid_usernames.append(match.group(1))
        else:
            # Capture any invalid URLs for feedback
            invalid_urls.append(url)
    
    return valid_usernames, invalid_urls

# Function to load data from a CSV URL with error handling
def load_csv_data(csv_url):
    """
    This function loads data from a CSV URL and returns a pandas DataFrame.
    It handles any potential CSV parsing errors by skipping problematic rows.
    """
    try:
        # Read the CSV file from the provided URL and handle bad lines gracefully
        df = pd.read_csv(csv_url, on_bad_lines='skip')
        return df
    except Exception as e:
        # Display an error message if the CSV could not be loaded
        st.error(f"Error loading CSV: {e}")
        return pd.DataFrame()  # Return an empty DataFrame on error

# Function to query the CSV data with usernames
def query_database(usernames, df):
    """
    This function accepts a list of usernames and queries the CSV DataFrame
    to retrieve their 'unit_sold_last_30_days' and '% category' values.
    """
    results = []
    
    for username in usernames:
        # Search for the username in the DataFrame
        record = df[df['username'] == username]
        if not record.empty:
            # If the username is found, extract the relevant data
            results.append({
                "username": username,
                "unit_sold_last_30_days": record["unit_sold_last_30_days"].values[0],
                "% category": record["% category"].values[0]
            })
        else:
            # If the username is not found, mark it as "Not found"
            results.append({
                "username": username,
                "unit_sold_last_30_days": "Not found",
                "% category": "Not found"
            })
    
    return results

# Main function to run the Streamlit app
def main():
    # Title of the app
    st.title("TikTok Sales Data Analyzer")
    
    # Input field for the user to provide the CSV URL (Google Sheets CSV link)
    csv_url = st.text_input("Enter the CSV URL")
    
    # Multi-line text area for TikTok URLs input
    tiktok_urls = st.text_area(
        "TikTok Channel URLs", 
        placeholder="Enter TikTok channel URLs here, one per line."
    )
    
    # Button to process the URLs and fetch data
    if st.button("Extract Usernames and Query Data"):
        if csv_url and tiktok_urls:
            # Load the CSV data
            df = load_csv_data(csv_url)
            
            # Check if the DataFrame is successfully loaded (not empty)
            if not df.empty:
                # Split the input into individual lines (one URL per line)
                url_list = tiktok_urls.splitlines()
                
                # Extract TikTok usernames from the input URLs
                valid_usernames, invalid_urls = extract_tiktok_usernames(url_list)
                
                # Display the extracted valid usernames
                if valid_usernames:
                    st.success("Valid TikTok usernames extracted:")
                    st.write(valid_usernames)
                    
                    # Query the CSV for matching usernames and display the results
                    results = query_database(valid_usernames, df)
                    st.write("Usernames Data from CSV:")
                    st.dataframe(pd.DataFrame(results))
                
                # Display any invalid URLs that could not be processed
                if invalid_urls:
                    st.error("These URLs couldn't be processed as valid TikTok URLs:")
                    st.write(invalid_urls)
        else:
            st.warning("Please enter the CSV URL and TikTok URLs to process.")

# Run the app
if __name__ == "__main__":
    main()
