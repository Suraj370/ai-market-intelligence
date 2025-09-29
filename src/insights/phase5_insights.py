import pandas as pd
import numpy as np
import google.generativeai as genai
import pandas as pd
import numpy as np
import os
import google.generativeai as genai

def analyze_d2c_data_with_creatives(
    data, 
    cohort_freq="M",
    category_col="category",
    date_col="date",
    spend_col="spend",
    revenue_col="revenue",
    impressions_col="impressions",
    clicks_col="clicks",
    conversions_col="conversions",
    installs_col="installs",
    signups_col="signups",
    first_purchase_col="first_purchase",
    repeat_purchase_col="repeat_purchase"
):
    """
    Full D2C analysis: KPIs, SEO opportunities, retention, + AI-powered creative generation.

    Parameters:
        data (str | pd.DataFrame): Excel path or DataFrame
    
    Returns:
        dict: { "kpis", "seo_opportunity", "retention_summary", "creatives" }
    """

    # ---------------- Load Data ----------------
    if isinstance(data, str):
        df = pd.read_excel(data)
    else:
        df = data.copy()

    df.columns = [c.strip().lower() for c in df.columns]

    # ---- Auto Map Columns ----
    column_map = {
        "spend_usd": "spend",
        "revenue_usd": "revenue",
        "seo_category": "category",
        "avg_position": "average_position",
        "monthly_search_volume": "search_volume"
    }
    df.rename(columns=column_map, inplace=True)

    # ---- Handle Missing Date ----
    if date_col not in df.columns:
        df[date_col] = pd.Timestamp.today()  # fallback if date is missing

    df[date_col] = pd.to_datetime(df[date_col])

    # ---- Numeric Cleanup ----
    numeric_cols = [
        spend_col, revenue_col, impressions_col, clicks_col,
        installs_col, signups_col, first_purchase_col,
        repeat_purchase_col, "conversion_rate", "search_volume", "average_position"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # ---------------- KPI Computation ----------------
    total_spend = df[spend_col].sum()
    total_revenue = df[revenue_col].sum()
    total_impr = df[impressions_col].sum()
    total_clicks = df[clicks_col].sum()
    total_conv = df[first_purchase_col].sum() if first_purchase_col in df.columns else 0

    cac = total_spend / total_conv if total_conv else None
    roas = total_revenue / total_spend if total_spend else None
    ctr = total_clicks / total_impr if total_impr else None
    conv_rate = total_conv / total_clicks if total_clicks else None

    kpis = pd.DataFrame([{
        "Total Spend": total_spend,
        "Total Revenue": total_revenue,
        "Impressions": total_impr,
        "Clicks": total_clicks,
        "Conversions": total_conv,
        "CAC": cac,
        "ROAS": roas,
        "CTR": ctr,
        "Click→Conversion Rate": conv_rate
    }])

    # ---------------- SEO Opportunity ----------------
    seo_opportunity = pd.DataFrame()
    if category_col in df.columns and "search_volume" in df.columns:
        seo = df.groupby(category_col).agg({
            "search_volume": "sum",
            "average_position": "mean",
            "conversion_rate": "mean",
        }).reset_index()

        # Normalize and score
        seo["norm_vol"] = (seo["search_volume"] - seo["search_volume"].min()) / (seo["search_volume"].max() - seo["search_volume"].min() + 1e-9)
        seo["norm_pos"] = 1 - (seo["average_position"] / (seo["average_position"].max() + 1e-9))
        seo["norm_conv"] = (seo["conversion_rate"] - seo["conversion_rate"].min()) / (seo["conversion_rate"].max() - seo["conversion_rate"].min() + 1e-9)
        seo["opportunity_score"] = seo["norm_vol"]*0.5 + seo["norm_pos"]*0.3 + seo["norm_conv"]*0.2
        seo_opportunity = seo.sort_values("opportunity_score", ascending=False)

    # ---------------- Retention Summary ----------------
    retention_summary = {}
    if first_purchase_col in df.columns and repeat_purchase_col in df.columns:
        first = df[first_purchase_col].sum()
        repeat = df[repeat_purchase_col].sum()
        retention_summary = {
            "first_purchases": first,
            "repeat_purchases": repeat,
            "repeat_rate": repeat / first if first else 0
        }

    # ---------------- Creative Generation ----------------
    creatives = []
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.5-flash")

        for _, row in seo_opportunity.head(3).iterrows():
            prompt = f"""
            Generate 3 marketing creatives for this D2C category.

            INSIGHTS:
            - Category: {row[category_col]}
            - ROAS: {roas:.2f}, CAC: {cac:.2f}
            - Repeat Rate: {retention_summary.get('repeat_rate', 'N/A')}
            - SEO: Volume={row['search_volume']}, AvgPos={row['average_position']:.2f}, ConvRate={row['conversion_rate']:.2f}

            TASKS:
            1) Write 1 ad headline (max 10 words).
            2) Write 1 SEO meta description (max 160 chars).
            3) Write 1 product page snippet (50-70 words).

            Return ONLY valid JSON with keys: ad_headline, seo_meta, pdp_snippet
            No extra text, no markdown, no code fences.
            """

            response = model.generate_content(prompt)
            raw_text = response.text.strip()

            # Remove any accidental markdown fences or backticks
            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1]  # keep inside code
            raw_text = raw_text.replace("```json", "").replace("```", "").strip()

            # Try to parse JSON safely
            try:
                import json
                creative_json = json.loads(raw_text)
            except:
                creative_json = {"ad_headline": "", "seo_meta": "", "pdp_snippet": ""}

            creatives.append(creative_json)

    # ---------------- Return All Outputs ----------------
    return {
        "kpis": kpis,
        "seo_opportunity": seo_opportunity,
        "retention_summary": retention_summary,
        "creatives": creatives
    }
