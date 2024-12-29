import streamlit as st
from apify_client import ApifyClient
import pandas as pd
from datetime import datetime, timedelta

# Replace with your actual API token
client = ApifyClient("apify_api_GbQtNrgqcGpCAAb849rssoFyGhgb0W11hN7U")

def get_user_input():
    urls = st.text_area("Enter URLs separated by commas", key="url_input")  # Unique key
    urls = [url.strip() for url in urls.split(",")]
    start_date = st.date_input("Start Date", key="date_input")  # Unique key
    return urls, start_date

def prepare_actor_input(urls, start_date):
    # Convert start_date to ISO format and subtract one day
    one_day_ago = datetime.combine(start_date, datetime.min.time())
    formatted_date = one_day_ago.isoformat()

    run_input = {
        "startUrls": [{'url': url} for url in urls],
        "maxReviews": 100,
        "reviewsSort": "newest",
        "language": "id",
        "reviewsOrigin": "all",
        "reviewsStartDate": formatted_date,
        "personalData": True,
    }
    return run_input

def run_and_download(urls, start_date):
    run_input = prepare_actor_input(urls, start_date)
    run = client.actor("Xb8osYTtOjlsgI6k9").call(run_input=run_input)

    dataset = client.dataset(run["defaultDatasetId"])
    data = [item for item in dataset.iterate_items()]
    df = pd.DataFrame(data)

    # Save as Excel
    excel_file = "reviews.xlsx"
    df.to_excel(excel_file, index=False)
    with open(excel_file, "rb") as file:
        st.download_button(
            label="Download data as Excel",
            data=file,
            file_name='reviews.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

# Main application logic
urls, start_date = get_user_input()  # Call only once
if st.button("Run Review Scraper"):
    run_and_download(urls, start_date)
