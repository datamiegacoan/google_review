import streamlit as st
from apify_client import ApifyClient
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo  #Bawaan Python 3.9 ke atas.

client = ApifyClient(st.secrets["APIFY_TOKEN"])
ACTOR_ID = "Xb8osYTtOjlsgI6k9"

def get_user_input():
    urls_text = st.text_area("Enter URLs separated by commas")
    urls = [url.strip() for url in urls_text.split(",") if url.strip()]
    start_date = st.date_input("Start date (in WIB)")
    return urls, start_date

def prepare_actor_input(urls, start_date):
    #Penggabungan input tanggal dengan jam 00:00:00 lokal.
    local_dt = datetime.combine(start_date, datetime.min.time())
    
    #Penandaan bahwa jam 00:00:00 ini adalah zona waktu WIB (Asia/Jakarta).
    wib_dt = local_dt.replace(tzinfo=ZoneInfo("Asia/Jakarta"))
    
    #Konversi Waktu dari WIB ke UTC (Zulu Time).
    utc_dt = wib_dt.astimezone(ZoneInfo("UTC"))
    
    #Format Waktu menjadi string ISO yang dikenali Apify Actor.
    formatted_date = utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    
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

        #Tampung properti object Pydantic.
        dataset_id = run.default_dataset_id

        if not dataset_id:
            st.error("Actor tidak menghasilkan dataset.")
            st.write("Run result:")
            st.write(run) 
            return

        data = list(client.dataset(dataset_id).iterate_items())

        if not data:
            st.warning("Scraping selesai, tapi tidak ada data review.")
            return

        df = pd.DataFrame(data)

        #=== PROSES KONVERSI OUTPUT ZULU TIME KE WIB ===
        nama_kolom_tanggal = "publishedAtDate"
        
        if nama_kolom_tanggal in df.columns:
            try:
                #Ubah kolom text string menjadi datetime object Pandas (Pandas otomatis membaca 'Z' sebagai UTC/Zulu Time).
                df[nama_kolom_tanggal] = pd.to_datetime(df[nama_kolom_tanggal], errors='coerce')
                
                #Konversi dari UTC ke Asia/Jakarta (WIB).
                #.dt.tz_localize(None) dipakai untuk menghapus flag zona waktu (+07:00) agar nanti terbaca sebagai date, bukan string di Excel.
                df[nama_kolom_tanggal] = df[nama_kolom_tanggal].dt.tz_convert('Asia/Jakarta').dt.tz_localize(None)
            except Exception as tz_err:
                st.warning(f"Gagal mengonversi kolom {nama_kolom_tanggal} ke WIB. Menampilkan format bawaan.")
        #===============================================

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
