#Source: https://github.com/mkhorasani/Streamlit-Authenticator?ref=blog.streamlit.io
import streamlit as st
import global_state_lib as gsl
import lib
from streamlit_js_eval import streamlit_js_eval
from yaml.loader import SafeLoader
import yaml
import os


# Load the global state
global_state = gsl.get_global_state()

with open('src/credentials.yml') as file:
    config = yaml.load(file, Loader=SafeLoader)

if 'Login' in global_state.get_key_names() and global_state['Login']: #Allow to logout
    st.markdown("#### Logout")
    logout = st.button("Logout")
    if logout: #load public data
        product_id = global_state['product_id']
        global_state['Login'] = False
        fd = lib.communication()
        fd.fetch_data(product_id)
        if global_state['status'] == 'OK':              
            if 'pages_loaded' in global_state.get_key_names() and global_state['pages_loaded']:           
                st.switch_page(os.path.join('web_pages', 'general_product_and_manufacturer_information.py'))
else:
    st.markdown("#### Enter your credentials")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    submit = st.button("Login")
    st.markdown(':blue[You can test with the] ')
    st.markdown(':blue[User: private and Password: abc]')
    psw = config['credentials']['private']['password']
    if submit:
        if username == 'private' and password == psw: #login successful
            global_state['Login'] = True
            product_id = global_state['product_id']
            fd = lib.communication()
            fd.fetch_data(product_id)
            if global_state['status'] == 'OK':              
                if 'pages_loaded' in global_state.get_key_names() and global_state['pages_loaded']:           
                    st.switch_page(os.path.join('web_pages', 'general_product_and_manufacturer_information.py'))
        else:
            st.error('Username/password is incorrect')