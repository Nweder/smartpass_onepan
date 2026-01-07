import streamlit as st
import os

# ----- GLOBAL CSS -----
st.markdown("""
<style>
    /* Background video container */
    .main .block-container {
        padding-top: 5vh !important;
        padding-bottom: 5vh !important;
    }

    /* Center content vertically and horizontally */
    [data-testid="stVerticalBlock"] {
        align-items: center;
        justify-content: center;
        min-height: 80vh;
    }

    h1 {
        text-align: center;
        color: #fff;
        font-size: 3.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
    }

    p, .stMarkdown {
        text-align: center;
        color: #fff;
        font-size: 1.5rem;
        max-width: 600px;
        margin: 0 auto 2.5rem auto;
    }

    /* Full-width button styles */
    .full-btn {
        width: 100%;
        display: block;
        background: rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);

        border: 1px solid rgba(255,255,255,0.3);
        border-radius: 50px;

        padding: 20px 0;
        text-align: center;

        color: #fff !important;
        font-size: 1.5rem;
        font-weight: 600;

        text-decoration: none !important;      /* NE-podtržené */
        white-space: nowrap;                   /* vše v jednom řádku */

        cursor: pointer;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        transition: all 0.25s ease;
    }

    .full-btn:hover {
        background: rgba(255,255,255,0.35);
        box-shadow: 0 6px 20px rgba(0,0,0,0.08);
    }

</style>
""", unsafe_allow_html=True)



# ----- PAGE CONTENT -----

st.title("Welcome to OnePan Smartpass!")
st.write("Explore your product's history.")


# Full-width button (custom HTML)
st.markdown(
    f"""
        <a href="product_id" class="full-btn" target="_self">🔍 Search Product</a>
    """,
    unsafe_allow_html=True
)


