import pandas as pd
import numpy as np
def clean_google_play_data(filepath):
    """
    Loads the Google Play Store dataset, performs cleaning, normalization,
    and conversion of key columns, and returns the cleaned DataFrame.

    The cleaning steps include:
    1. Handling the known row error (row 10472).
    2. Removing duplicate app entries, keeping the latest update.
    3. Filling missing values in key columns.
    4. Normalizing and converting 'Reviews', 'Size', 'Installs', and 'Price' 
       to appropriate numeric data types.

    Args:
        filepath (str): The path to the 'googleplaystore.csv' file.

    Returns:
        pd.DataFrame: The cleaned and structured DataFrame.
    """
    
    
    try:
        # Read directly from the file object provided by st.file_uploader
        df = pd.read_csv(filepath)
    except Exception as e:
        return pd.DataFrame()

    # --- Initial Cleaning and Error Handling ---
    df.drop(df[df['App'] == 'Life is Strange'].index, inplace=True, errors='ignore')

    # --- Duplicate Removal ---
    df.drop_duplicates(subset=['App'], keep='last', inplace=True)

    # --- Missing Value Imputation ---
    df['Rating'].fillna(df['Rating'].mean(), inplace=True)
    df['Type'].fillna('Free', inplace=True)
    df['Content Rating'].fillna('Everyone', inplace=True)

    # --- Data Normalization and Type Conversion ---
    df['Reviews'] = pd.to_numeric(df['Reviews'], errors='coerce')

    # Convert 'Installs' to integer
    df['Installs'] = df['Installs'].astype(str).str.replace('+', '', regex=False)
    df['Installs'] = df['Installs'].str.replace(',', '', regex=False)
    df['Installs'] = pd.to_numeric(df['Installs'], errors='coerce', downcast='integer')

    # Convert 'Price' to float
    df['Price'] = df['Price'].astype(str).str.replace('$', '', regex=False)
    df['Price'] = pd.to_numeric(df['Price'], errors='coerce').fillna(0.0)
    df['platform_android'] = 'Android'

    # Convert 'Size' to float (in MB)
    def normalize_size(size):
        if pd.isna(size) or str(size) == 'Varies with device':
            return np.nan
        size = str(size).replace(',', '')
        if 'M' in size:
            return float(size.replace('M', ''))
        elif 'k' in size:
            return float(size.replace('k', '')) / 1024
        return np.nan

    df['Size_MB'] = df['Size'].apply(normalize_size)
    df.drop('Size', axis=1, inplace=True)

    # Normalize app name for merging (CRITICAL: MUST match iOS normalization logic)
    df['App'] = df['App'].astype(str).str.lower().str.split('[\-:\(]').str[0].str.strip()

    df.rename(columns={'App': 'app_name', 'Category': 'category', 'Rating': 'android_rating',
                       'Reviews': 'android_review_count', 'Installs': 'android_installs', 'Type': 'android_type',
                       'Price': 'android_price', 'Content Rating': 'android_content_rating',
                       'Current Ver': 'android_current_version', 'Android Ver': 'android_version',
                       'Size_MB': 'android_size'}, inplace=True)

    return df.drop_duplicates(subset=['app_name'], keep='last').reset_index(drop=True)
