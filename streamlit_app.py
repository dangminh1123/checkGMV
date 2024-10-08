# Import necessary libraries
import streamlit as st
import pandas as pd
import re
import logging

# Configure logging to capture errors
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Function to extract TikTok usernames from a list of inputs
def extract_tiktok_usernames(inputs):
    """
    Extracts TikTok usernames from URLs or accepts them directly.
    """
    pattern = re.compile(r"(?:https?://)?(?:www\.)?tiktok\.com/@([A-Za-z0-9_.]+)")
    valid_usernames = []
    invalid_inputs = []

    for line in inputs:
        line = line.strip()
        if not line:
            continue  # Skip empty lines
        match = pattern.match(line)
        if match:
            valid_usernames.append(match.group(1))
        elif re.match(r"^[A-Za-z0-9_.]+$", line):
            # Line is a valid username
            valid_usernames.append(line)
        else:
            invalid_inputs.append(line)

    return valid_usernames, invalid_inputs

# Function to load data from a CSV URL
@st.cache_data(show_spinner=False)
def load_csv_data(csv_url):
    """
    Loads data from a CSV export link from Google Sheets.
    """
    try:
        df = pd.read_csv(csv_url, dtype={'phone': str})
        return df
    except Exception as e:
        logger.error(f"Error loading CSV: {e}")
        st.error(f"Error loading CSV: {e}")
        return pd.DataFrame()

# Function to query the CSV data with usernames
def query_database(usernames, df):
    """
    Queries the DataFrame for the given usernames.
    """
    results = []
    not_found_count = 0
    usernames_not_found = []
    required_columns = [
        'username', 'unit_sold_last_30_days', '% category', 'brand', 'phone', 'email'
    ]

    # Check for required columns
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        st.error(f"Missing columns in CSV: {', '.join(missing_columns)}")
        logger.error(f"Missing columns in CSV: {missing_columns}")
        return results, len(usernames), []

    # Use pandas merge for efficient querying
    usernames_df = pd.DataFrame({'username': usernames})
    merged_df = usernames_df.merge(df, on='username', how='left', indicator=True)

    for i, row in merged_df.iterrows():
        if row['_merge'] == 'both':
            # Process phone number
            phone_number = str(row["phone"])
            # Remove any non-digit characters
            phone_number = re.sub(r'\D', '', phone_number)
            # Ensure phone number is 10 characters long and starts with '0'
            if not phone_number.startswith('0'):
                phone_number = '0' + phone_number
            phone_number = phone_number[-10:].zfill(10)

            # Process unit_sold_last_30_days
            unit_sold = row["unit_sold_last_30_days"]
            if pd.notnull(unit_sold) and isinstance(unit_sold, (int, float)):
                unit_sold = int(unit_sold)
            else:
                unit_sold = "Not found"

            results.append({
                "Record #": i + 1,
                "username": row['username'],
                "unit_sold_last_30_days": unit_sold,
                "% category": row["% category"],
                "brand": row["brand"],
                "phone": phone_number,
                "email": row["email"]
            })
        else:
            not_found_count += 1
            usernames_not_found.append(row['username'])
            results.append({
                "Record #": i + 1,
                "username": row['username'],
                "unit_sold_last_30_days": "Not found",
                "% category": "Not found",
                "brand": "Not found",
                "phone": "Not found",
                "email": "Not found"
            })

    return results, not_found_count, usernames_not_found

# Main function to run the Streamlit app
def main():
    st.title("📊 TikTok Sales Data Analyzer")

    st.write("""
    This app allows you to input TikTok usernames or profile URLs and retrieve associated sales data from a CSV file.
    """)

    # Input field for the Google Sheets CSV export link
    st.header("Step 1: Enter CSV URL")
    csv_url = st.text_input(
        "Enter the Google Sheets CSV URL",
        help=(
            "Export your Google Sheets as CSV and paste the link here. "
            "Make sure the Google Sheet is shared publicly with view-only access."
        )
    )

    if csv_url:
        with st.spinner("Loading CSV data..."):
            df = load_csv_data(csv_url)
        if not df.empty:
            st.success("CSV data loaded successfully!")
            st.write(f"Data contains {df.shape[0]:,} records and {df.shape[1]} columns.")
        else:
            st.error("Failed to load CSV data. Please check the URL and try again.")
            return
    else:
        st.info("Please enter a valid CSV URL to proceed.")
        return

    # Input area for TikTok usernames or URLs
    st.header("Step 2: Enter TikTok Usernames or URLs")
    tiktok_input = st.text_area(
        "Input one username or URL per line.",
        placeholder="Example:\nusername1\nhttps://www.tiktok.com/@username2",
        height=200
    )

    # Process inputs when the button is clicked
    if st.button("🔍 Process and Query Data"):
        if not tiktok_input.strip():
            st.warning("Please enter at least one TikTok username or URL.")
        else:
            with st.spinner("Processing..."):
                input_list = tiktok_input.strip().splitlines()
                valid_usernames, invalid_inputs = extract_tiktok_usernames(input_list)

                if valid_usernames:
                    st.success(f"Extracted {len(valid_usernames)} valid username(s).")
                    # Query the CSV for matching usernames
                    results, not_found_count, usernames_not_found = query_database(valid_usernames, df)
                    results_df = pd.DataFrame(results)

                    # Display results
                    st.header("Query Results")
                    st.dataframe(results_df)

                    # Downloadable CSV of results
                    csv_data = results_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="⬇️ Download Results as CSV",
                        data=csv_data,
                        file_name='tiktok_query_results.csv',
                        mime='text/csv'
                    )

                    # If there are usernames not found, display and provide a CSV download
                    if usernames_not_found:
                        st.warning(f"Usernames not found in CSV ({not_found_count}):")
                        st.code('\n'.join(usernames_not_found))
                        # Downloadable CSV of usernames not found
                        not_found_df = pd.DataFrame({'username': usernames_not_found})
                        not_found_csv = not_found_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="⬇️ Download Usernames Not Found as CSV",
                            data=not_found_csv,
                            file_name='usernames_not_found.csv',
                            mime='text/csv'
                        )

                    # Summary
                    st.write(f"Total inputs processed: {len(input_list)}")
                else:
                    st.error("No valid TikTok usernames found in the input.")

                # Report invalid inputs
                if invalid_inputs:
                    st.warning("The following inputs were not recognized as valid TikTok usernames or URLs:")
                    st.write(invalid_inputs)

# Run the app
if __name__ == "__main__":
    main()
