import pandas as pd

def combine_datasets(android_df: pd.DataFrame, ios_df: pd.DataFrame) -> pd.DataFrame:
    """
    Performs an INNER join on the normalized app_name column to find
    only those apps that exist on both platforms.
    
    The merge uses only the 'app_name' to allow for different category names
    across platforms.
    """
    print("\n--- Performing Data Combine (Inner Join) ---")
    
    # FIX: Merge ONLY on the normalized 'app_name' column
    merged_df = pd.merge(
        android_df,
        ios_df,
        on='app_name',
        how='inner',
        suffixes=('_android', '_ios')
    )
    
    print(f"Merge complete. Cross-platform app count: {merged_df.shape[0]}")
    
    # Cleanup and reorder final columns for presentation
    # Note: We keep 'category_android' and rename it to 'Category'
    cols_to_keep = [
        'app_name', 
        'category_android',
        'android_rating', 'ios_rating',
        'android_review_count', 'ios_review_count',
        'android_price', 'ios_price',
        'android_installs',
        'android_size', 'ios_size',
        'android_content_rating', 'ios_content_rating'
    ]
    
    final_df = merged_df.loc[:, [col for col in cols_to_keep if col in merged_df.columns]]
    final_df.rename(columns={'category_android': 'Category'}, inplace=True)
    
    return final_df