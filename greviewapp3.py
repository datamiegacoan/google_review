import streamlit as st
from apify_client import ApifyClient
import pandas as pd
from datetime import datetime

client = ApifyClient(st.secrets["APIFY_TOKEN"])
ACTOR_ID = "Xb8osYTtOjlsgI6k9"

def get_user_input():
    urls_text = st.text_area("Enter URLs separated by commas")
    urls = [url.strip() for url in urls_text.split(",") if url.strip()]
    start_date = st.date_input("Start Date")
    return urls, start_date

def prepare_actor_input(urls, start_date):
    # Format tanggal pakai Zulu Time, bukan local time.
    formatted_date = datetime.combine(start_date, datetime.min.time()).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    return {
        "startUrls": [{"url": url} for url in urls],
        "maxReviews": 100,
        "reviewsSort": "newest",
        "language": "id",
        "reviewsOrigin": "all",
        "reviewsStartDate": formatted_date,
        "personalData": True,
    }

def run_and_download(urls, start_date):
    if not urls:
        st.error("URL belum diisi.")
        return

    run_input = prepare_actor_input(urls, start_date)

    try:
        with st.spinner("Running Apify actor..."):
            run = client.actor(ACTOR_ID).call(run_input=run_input)

        # Tampung properti object Pydantic, bukan pemanggilan dictionary objek Pydantic dengan get() (objek Pydantic itu class instances, jadi akses properti pakai dot, bukan key-based access.).
        dataset_id = run.default_dataset_id

        if not dataset_id:
            st.error("Actor tidak menghasilkan dataset.")
            st.write("Run result:")
            st.write(run) # Menampilkan objek langsung bila properti default_dataset_id kosong.
            return

        data = list(client.dataset(dataset_id).iterate_items())

        if not data:
            st.warning("Scraping selesai, tapi tidak ada data review.")
            return

        df = pd.DataFrame(data)

        excel_file = "reviews.xlsx"
        df.to_excel(excel_file, index=False)

        with open(excel_file, "rb") as file:
            st.download_button(
                label="Download data as Excel",
                data=file,
                file_name="reviews.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error("Terjadi error saat menjalankan scraper.")
        st.exception(e)

urls, start_date = get_user_input()

if st.button("Run Review Scraper"):
    run_and_download(urls, start_date)
