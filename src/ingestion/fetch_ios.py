import os
import pandas as pd
import requests
import numpy as np

def _parse_ios_response(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Internal function to parse raw iOS API response data into a structured and cleaned DataFrame."""
    try:
        
        # Handle Price conversion
        price_series = raw_df.get('Price', pd.Series(['0.00'] * len(raw_df)))
        price_series = price_series.apply(lambda x: str(x).replace('$', '').strip() if pd.notna(x) else '0.00')
        price_series = pd.to_numeric(price_series, errors='coerce').fillna(0.0)

        # Create parsed DataFrame
        parsed_df = pd.DataFrame({
            'app_name': raw_df.get('title', 'Unknown'),
            'category': raw_df.get('primaryGenreName', raw_df.get('genres', pd.Series(['Unknown'] * len(raw_df))).apply(lambda x: x[0] if isinstance(x, list) and x else 'Unknown')),
            'ios_rating': pd.to_numeric(raw_df.get('score', np.nan), errors='coerce'),
            'ios_review_count': pd.to_numeric(raw_df.get('reviews', 0), errors='coerce').fillna(0).astype(int),
            'ios_size': raw_df.get('size', np.nan),
            'ios_installs': np.nan,
            'ios_type': raw_df.get('free', pd.Series([True] * len(raw_df))).apply(lambda x: 'Free' if x else 'Paid'),
            'ios_price': price_series,
            'ios_last_updated': pd.to_datetime(raw_df.get('updated'), errors='coerce').dt.strftime('%Y-%m-%d'),
            'ios_content_rating': raw_df.get('contentRating', 'Everyone'),
            'ios_version': raw_df.get('requiredOsVersion', 'Varies with device'),
            'platform_ios': 'iOS'
        })

        # --- CRITICAL: Normalize app name for efficient merging ---
        parsed_df['app_name'] = parsed_df['app_name'].astype(str).str.lower().str.split('[\-:\(]').str[0].str.strip()

        return parsed_df.drop_duplicates(subset=['app_name'], keep='last').reset_index(drop=True)

    except Exception as e:
        print(f"Error parsing iOS response: {e}")
        raise


def fetch_ios_data(query: str, num_apps: int = 50, lang: str = "en", country: str = "us") -> pd.DataFrame:
    """
    Fetches a broad sample of app data from the iOS App Store API and cleans it.
    Requires the RAPIDAPI_KEY environment variable to be set.
    """

    API_URL = "https://appstore-scrapper-api.p.rapidapi.com/v1/app-store-api/search"
    HEADERS = {
        "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
        "x-rapidapi-host": "appstore-scrapper-api.p.rapidapi.com"
    }

    querystring = {
        "num": str(num_apps),
        "lang": lang,
        "query": query,
        "country": country
    }

    try:
        print(f"Fetching iOS data for query: '{query}'...")
        # Check if API key is present before making the request
        if not os.getenv("RAPIDAPI_KEY"):
            print("Warning: RAPIDAPI_KEY is not set. Cannot fetch live iOS data.")
            return pd.DataFrame()
            
        response = requests.get(API_URL, headers=HEADERS, params=querystring, timeout=20)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            print(f"Successfully fetched {len(data)} iOS apps.")
            raw_df = pd.DataFrame(data)
            return _parse_ios_response(raw_df)
        else:
            print("API response was not a list of apps.")
            return pd.DataFrame()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching iOS data: {e}")
        return pd.DataFrame()