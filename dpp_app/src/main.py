import streamlit as st
import os
import lib
import global_state_lib as gsl

# global state is always ONEPan
st.set_page_config(page_title="Digital Product Passport", page_icon=":material/edit:", layout='wide')
global_state = gsl.get_global_state()
global_state['company'] = 'ONEPan'

# Initialize current page in session state
if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"

# always show product ID and user login pages in the sidebar
pages = []
pages.append(st.Page("web_pages/home.py", title="Home", icon=":material/home:"))

# get the name of the logo image - ONEPan
path_image = os.path.join(os.getcwd(), os.path.join("images", global_state['company']))
files = [f for f in os.listdir(path_image) if os.path.isfile(os.path.join(path_image, f)) and 'logo' in str(f)]
if files:
    st.sidebar.image(os.path.join(path_image, files[0]), caption=global_state['company'])

global_state['pages_loaded'] = False

# If Product_ID is in query params, fetch data automatically (only once)
if 'Product_ID' in st.query_params and not ('request' in st.session_state.keys()):
    st.session_state['request'] = False
    product_id = st.query_params['Product_ID']
    fd = lib.communication()
    fd.fetch_data(product_id)

# Dynamically create pages based on metadata if data fetch was successful
if 'status' in global_state.get_key_names() and global_state['status'] == 'OK':
    function_names = list(
        global_state['metadata_data_content_pages'][category]['function_name']
        for category in global_state['metadata_data_content_pages'].keys()
    )
    lib.create_generic_page_py(function_names)
    i = 0

    for page in global_state['metadata_data_content_pages'].keys():
        pages.append(
            st.Page(
                'web_pages/' + function_names[i] + '.py',
                title=page,
                icon=global_state['metadata_data_content_pages'][page]['icon_category']
            )
        )
        i += 1
    global_state['pages_loaded'] = True

pages.append(st.Page("web_pages/product_id.py", title="Enter Product ID", icon=":material/verified_user:"))

# Determine the title for user login page
login_title = "User Login"
if 'Login' in global_state.get_key_names() and global_state['Login'] and 'username' in global_state.get_key_names():
    login_title = global_state['username']

pages.append(st.Page("web_pages/user_login.py", title=login_title, icon=":material/passkey:"))

# NAVIGATION
pg = st.navigation(pages)
current_page = pg.title if pg.title != "" else "Home"
global_state["current_page_name"] = current_page
st.session_state.current_page = current_page


# ----- BACKGROUND VIDEO -----
is_home = (st.session_state.current_page == "Home")
video_class = "video-home" if is_home else "video-other"

st.markdown(
    f"""
    <style>

    .stApp {{
        background: transparent;
    }}

    #video-container {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        z-index: -1;
        overflow: hidden;
    }}

    #background-video {{
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
        transition: all 0.5s ease;
    }}

    .video-home {{
        opacity: 0.4 !important;
        filter: none !important;
    }}

    .video-other {{
        opacity: 0.15 !important;
        filter: blur(12px) !important;
    }}
    </style>

    <div id="video-container">
        <video id="background-video" autoplay loop muted playsinline class="{video_class}">
            <source src="https://www.pexels.com/download/video/3768941/" type="video/mp4">
            Your browser does not support the video tag.
        </video>
    </div>
    """,
    unsafe_allow_html=True
)

# RUN PAGE
pg.run()
