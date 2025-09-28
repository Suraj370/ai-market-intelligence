import json
import streamlit as st
import pandas as pd
from src.ingestion import clean_google_play_data, fetch_ios_data, combine_datasets
from src.insights import generate_insights
from src.reports import generate_report
from dotenv import load_dotenv

load_dotenv()
def main():
    st.title("Market Intelligence Dashboard")
    st.write("Welcome to the Market Intelligence Dashboard. Here you can analyze market trends and data.")


    st.sidebar.header("Navigation")
    page = st.sidebar.radio("Go to", ["Data Ingestion & Processing", "Insights", "Dataset", "Report"])

    if 'android_df' not in st.session_state:
        st.session_state.android_df = pd.DataFrame()
    if 'ios_df' not in st.session_state:
        st.session_state.ios_df = pd.DataFrame()

    if 'combined_df' not in st.session_state:
        st.session_state.combined_df = pd.DataFrame()
    if 'insights_data' not in st.session_state:
        st.session_state.insights_data = {}
    if 'report_path' not in st.session_state:
        st.session_state.report_path = None

    if page == "Data Ingestion & Processing":
        st.header("Ingest and Process Data")
        android_file = st.file_uploader("Upload your CSV file", type=["csv"])
        if android_file is not None:
             
            st.session_state.android_df = clean_google_play_data(android_file)
            st.write("Data Preview:")
            st.dataframe(st.session_state.android_df.head())
            st.success("Data ingested successfully!")
            

        
        st.subheader("2. iOS Data Fetch (App Store)")
        
        col1, col2 = st.columns(2)
        with col1:
            query = st.text_input("Enter broad category for iOS search (e.g., 'Social', 'Game')", value="Social")
            country = st.text_input("Country code (e.g., 'us')", value="us")
        with col2:
            num_apps = st.number_input("Number of apps to fetch per query (Max 200)", min_value=1, max_value=200, value=50)
            language = st.text_input("Language code (e.g., 'en')", value="en")
        
        # Add button to trigger the fetch operation
        if st.button("Fetch iOS Data & Merge to Session", type="primary"):
            if st.session_state.android_df.empty:
                 st.warning("Please upload and clean Android data first to ensure normalization works correctly.")
            
            with st.spinner(f"Fetching {num_apps} iOS apps for query '{query}'..."):
                try:
                    ios_df = fetch_ios_data(query=query, num_apps=num_apps, country=country, lang=language)
                    
                    if not ios_df.empty:
                        # Logic to append new data to existing session state data and remove duplicates
                        if not st.session_state.ios_df.empty:
                            st.session_state.ios_df = pd.concat([st.session_state.ios_df, ios_df]).drop_duplicates(subset=['app_name'])
                        else:
                            st.session_state.ios_df = ios_df

                        st.write("iOS Data Preview (latest fetched):")
                        st.dataframe(ios_df.head())
                        st.success(f"iOS data fetched successfully! Total unique iOS apps in session: {len(st.session_state.ios_df)}")
                    else:
                        st.warning(f"No iOS data was retrieved for query '{query}'. Please check your query parameters or API key.")
                except Exception as e:
                    st.error(f"Error fetching iOS data: {str(e)}")

        # 3. Combine Datasets
        st.subheader("3. Combine Datasets ")
        
        if st.button("Combine Datasets for Cross-Platform Analysis", type="secondary"):
            if st.session_state.android_df.empty or st.session_state.ios_df.empty:
                st.error("No data to combine. Please ingest Android data and fetch iOS data first.")
            else:
                with st.spinner("Combining datasets on normalized app name..."):
                    try:
                        st.session_state.combined_df = combine_datasets(
                            android_df=st.session_state.android_df, 
                            ios_df=st.session_state.ios_df
                        )
                        if not st.session_state.combined_df.empty:
                            st.write("Combined Dataset Preview (Cross-Platform Apps):")
                            st.dataframe(st.session_state.combined_df[['app_name', 'Category', 'android_rating', 'ios_rating', 'android_installs']].head())
                            st.success(f"Datasets combined successfully! Found {st.session_state.combined_df.shape[0]} cross-platform apps.")
                        else:
                            st.warning("Combined dataset is empty. Check if any app names match after normalization.")

                        st.session_state.insights_data = generate_insights(combine_df = st.session_state.combined_df)
                    except Exception as e:
                        st.error(f"Error combining datasets: {str(e)}")


    elif page == "Dataset":
        st.header("Cross-Platform App Dataset")
        if not st.session_state.combined_df.empty:
            st.write("Filter by category to view merged app data.")
            
            if 'Category' not in st.session_state.combined_df.columns:
                st.warning("Category information is not available in the merged dataset.")
                st.dataframe(st.session_state.combined_df)
            else:
                categories = st.session_state.combined_df['Category'].dropna().unique()
                selected_category = st.selectbox("Select Category", ['All'] + list(categories))

                if selected_category == 'All':
                    st.dataframe(st.session_state.combined_df)
                else:
                    filtered_df = st.session_state.combined_df[st.session_state.combined_df['Category'] == selected_category]
                    st.dataframe(filtered_df)
        else:
            st.write("No dataset available. Process data first on the 'Data Ingestion & Processing' page.")
            
    elif page == "Insights":
        st.header("📊 Insights & Analysis")
        # Check if insights data exists in the session state
        if "insights_data" in st.session_state and st.session_state.insights_data:
            insights_data = st.session_state.insights_data
            
            # Display the statistical summary table
            if "stats_table" in insights_data and not insights_data["stats_table"].empty:
                st.subheader("Statistical Summary")
                st.dataframe(insights_data["stats_table"])

            # Display the AI-generated summary
            if "summary" in insights_data:
                st.subheader("Executive Insights")
                st.markdown(insights_data["summary"])
            
            # ------------------
            # Export Data section - now correctly placed
            # ------------------
        
            st.subheader("📥 Export Data")
        
            # Create a JSON-safe version of the insights data for download
            # This is the crucial fix for the TypeError
            json_insights_data = {
             "stats_table": insights_data["stats_table"].to_dict(orient='records'),
             "summary": insights_data.get("summary", "No summary available.")
             }

            # Convert the JSON-safe dictionary to a JSON string
            json_str = json.dumps(json_insights_data, indent=2)

        # Create the download button
            st.download_button(
                label="Download Insights as JSON",
                data=json_str,
                file_name="insights_report.json",
                mime="application/json"
            )
        else:
        # Message to display if no insights data is available
            st.warning("No insights available. Please go to the 'Analyze Data' page to run the analysis first.")
        
   
    
    
   
    elif page == "Report":
        st.header("📄 Report Generation")
        # Check for the existence and type of insights data
        if "insights_data" in st.session_state and isinstance(st.session_state.insights_data, dict) and st.session_state.insights_data:
            insights = st.session_state.insights_data

            report_format = st.selectbox("Choose Report Format", ["Markdown", "HTML", "PDF"])

            st.subheader("Preview")
        
            # This try-except block handles any potential errors during report generation
            try:
                download_data = None
                download_label = ""
                download_file_name = ""
                download_mime = ""
            
                # --- Markdown Report ---
                if report_format == "Markdown":
                    report_content = generate_report(insights, "md")
                    st.code(report_content, language="markdown")
                    download_data = report_content
                    download_label = "Download Markdown"
                    download_file_name = "insights_report.md"
                    download_mime = "text/markdown"

            # --- HTML Report ---
                elif report_format == "HTML":
                    report_content = generate_report(insights, "html")
                    st.code(report_content, language="html")
                    download_data = report_content
                    download_label = "Download HTML"
                    download_file_name = "insights_report.html"
                    download_mime = "text/html"

            # --- PDF Report ---
                elif report_format == "PDF":
                    pdf_path = generate_report(insights, "pdf")
                    st.info(f"PDF generated: {pdf_path}")
                
                    with open(pdf_path, "rb") as f:
                        download_data = f.read()
                        download_label = "Download PDF"
                        download_file_name = "insights_report.pdf"
                        download_mime = "application/pdf"
            
            # --- Consolidated Download Button ---
            # This is outside the if/elif blocks to avoid code duplication
                st.subheader("Download Report")
                if download_data: # Only show the button if data is ready
                    st.download_button(
                    label=download_label,
                    data=download_data,
                    file_name=download_file_name,
                    mime=download_mime
                )

            except Exception as e:
                st.error(f"An unexpected error occurred: {e}. The 'insights' variable might have been corrupted.")
        else:
            st.warning("No insights found or invalid data format. Please go to the 'Data Ingestion & Processing' page and run the analysis first.")

if __name__ == "__main__":
    main()
