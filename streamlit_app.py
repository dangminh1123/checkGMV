# Import necessary libraries
import streamlit as st
import pandas as pd
import re
import logging

# Configure logging to capture errors
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Function to extract TikTok usernames from a list of URLs
def extract_tiktok_usernames(urls):
    """
    This function takes a list of TikTok channel URLs, extracts the usernames,
    and provides feedback for any URLs that couldn't be processed.
    """
    pattern = re.compile(r"(?:https?://)?(?:www\.)?tiktok\.com/@([A-Za-z0-9_.]+)")
    valid_usernames = []
    invalid_urls = []

    # Loop through each URL and attempt to extract the username
    for url in urls:
        match = pattern.match(url.strip())
        if match:
            valid_usernames.append(match.group(1))
        else:
            invalid_urls.append(url)
    
    return valid_usernames, invalid_urls

# Function to load data from a Google Sheets CSV link
@st.cache_data
def load_csv_data(csv_url):
    """
    This function loads data from a CSV export link from Google Sheets
    and returns a pandas DataFrame. The data is cached to improve performance.
    """
    try:
        # Read the CSV file from the provided URL
        df = pd.read_csv(csv_url)
        return df
    except Exception as e:
        # Log and display an error message if the CSV could not be loaded
        logger.error(f"Error loading CSV: {e}")
        st.error(f"Error loading CSV: {e}")
        return pd.DataFrame()  # Return an empty DataFrame on error

# Function to query the CSV data with usernames
def query_database(usernames, df):
    """
    This function accepts a list of usernames and queries the CSV DataFrame
    to retrieve their 'unit_sold_last_30_days', '% category', and 'brand' values.
    """
    results = []
    not_found_count = 0

    for i, username in enumerate(usernames, start=1):  # Start index from 1
        # Use the correct column name 'username'
        if 'username' in df.columns:
            record = df[df['username'] == username]
            if not record.empty:
                results.append({
                    "Record #": i,  # Start record count from 1
                    "username": username,
                    "unit_sold_last_30_days": record["unit_sold_last_30_days"].values[0],
                    "% category": record["% category"].values[0],
                    "brand": record["brand"].values[0]
                })
            else:
                # If the username is not found, mark it as "Not found"
                not_found_count += 1
                results.append({
                    "Record #": i,
                    "username": username,
                    "unit_sold_last_30_days": "Not found",
                    "% category": "Not found",
                    "brand": "Not found"
                })
        else:
            st.error("The 'username' column is missing in the CSV data.")
            logger.error("The 'username' column is missing in the CSV data.")
            break
    
    return results, not_found_count

# Main function to run the Streamlit app
def main():
    # Title of the app
    st.title("TikTok Sales Data Analyzer")
    
    # Input field for the Google Sheets CSV export link
    csv_url = st.text_input(
        "Enter the Google Sheets CSV URL",
        help="Export your Google Sheets as CSV and paste the link here. "
             "Make sure the Google Sheet is shared publicly with view-only access."
    )

    # Load the CSV data if the URL is provided
    if csv_url:
        df = load_csv_data(csv_url)
        
        # Check if DataFrame is successfully loaded (not empty)
        if not df.empty:
            # Multi-line text area for TikTok URLs input
            tiktok_urls = st.text_area(
                "TikTok Channel URLs", 
                placeholder="Enter TikTok channel URLs here, one per line."
            )

            # Button to process the URLs and fetch data
            if st.button("Extract Usernames and Query Data"):
                if tiktok_urls:
                    # Split the input into individual lines (one URL per line)
                    url_list = tiktok_urls.splitlines()

                    # Extract TikTok usernames from the input URLs
                    valid_usernames, invalid_urls = extract_tiktok_usernames(url_list)

                    # Display the extracted valid usernames in a copiable code block
                    if valid_usernames:
                        st.success("Valid TikTok usernames extracted:")
                        st.code("\n".join(valid_usernames), language='python')  # Copiable code block for usernames
                        
                        # Query the CSV for matching usernames and display the results
                        results, not_found_count = query_database(valid_usernames, df)
                        st.write("Usernames Data from Google Sheets:")
                        st.dataframe(pd.DataFrame(results))

                        # Report summary of links processed and not found
                        st.write(f"Total links processed: {len(url_list)}")
                        st.write(f"Total usernames not found: {not_found_count}")

                    # Display any invalid URLs that could not be processed
                    if invalid_urls:
                        st.error("These URLs couldn't be processed as valid TikTok URLs:")
                        st.write(invalid_urls)
                else:
                    st.warning("Please enter the TikTok URLs to process.")
    else:
        st.info("Please enter a valid CSV URL to proceed.")

# Run the app
if __name__ == "__main__":
    main()
