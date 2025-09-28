import json
import streamlit as st
import pandas as pd
import numpy as np
from scipy import stats
import google.generativeai as genai
import os


# --------------- Core Functions ---------------
def compute_confidence_scores(df):
    """
    Compute mean, std, confidence intervals, p-values, and effect size for numeric columns.
    Returns: DataFrame with statistical metrics.
    """
    results = []
    numeric_cols = df.select_dtypes(include=np.number).columns

    for col in numeric_cols:
        data = df[col].dropna()
        if len(data) < 2:  # Skip tiny samples
            continue

        mean_val = np.mean(data)
        std_val = np.std(data, ddof=1)
        n = len(data)

        # 95% CI using t-distribution
        ci_low, ci_high = stats.t.interval(0.95, n-1, loc=mean_val, scale=std_val/np.sqrt(n))

        # One-sample t-test (baseline mean = 0)
        t_stat, p_val = stats.ttest_1samp(data, 0)

        # Effect Size (Cohen's d)
        cohen_d = mean_val / std_val if std_val > 0 else 0

        results.append({
            "Metric": col,
            "Mean": round(mean_val, 2),
            "Std Dev": round(std_val, 2),
            "95% CI": f"[{ci_low:.2f}, {ci_high:.2f}]",
            "p-Value": round(p_val, 4),
            "Effect Size": round(cohen_d, 3)
        })

    return pd.DataFrame(results)

def interpret_with_gemini(stats_df):
    """
    Send statistical summary to Gemini for natural language insights.
    """
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 
    genai.configure(api_key=GEMINI_API_KEY)
    if stats_df.empty:
        return "No numeric metrics found for statistical analysis."

    prompt = f"""
    Here is the statistical summary:
    {stats_df.to_string(index=False)}

    Please write a clear, concise executive summary highlighting:
    - Metrics with significant p-values (< 0.05)
    - Metrics with high or low effect sizes
    - Confidence intervals interpretation
    - Key takeaways for decision-makers

    Provide actionable recommendations based on these insights.

    """

    response = genai.GenerativeModel("gemini-2.5-flash").generate_content(prompt)
    return response.text

def run_insights_pipeline(combine_df: pd.DataFrame) -> dict:
    """
    Full pipeline: Compute stats → Interpret with Gemini → Return structured data
    """
    stats_df = compute_confidence_scores(combine_df)
    summary = interpret_with_gemini(stats_df)

    insights_data = {
        "stats_table": stats_df,
        "summary": summary
        
    }
    return insights_data