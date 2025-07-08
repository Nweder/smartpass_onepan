import streamlit as st
import lib
import os
import global_state_lib as gsl
from streamlit_js_eval import streamlit_js_eval
from streamlit.file_util import get_main_script_directory, normalize_path_join
from streamlit_cookies_controller import CookieController

from streamlit.runtime.scriptrunner import (
    RerunData,
    ScriptRunContext,
    get_script_run_ctx,
)
# Load the global state
global_state = gsl.get_global_state()

#Input digital product passport ID
#st.title('Welcome to the Digital Product Passport')
product_id = st.text_input('Enter the product ID here')
#Button to submit the product ID
st.markdown(''':blue[You can test with the Product IDs:]''')
st.markdown(''':blue[1]''')
global_state['scan_product_loaded']= True
if st.button('Submit'):
    fd = lib.communication()
    fd.fetch_data(product_id)
    if global_state['status'] == 'OK':
        st.write('You have successfully submitted the product ID')
        st.write('Please navigate to the next page for more information')  
        global_state['save_changes'] = False #This is to remove the button save changes in product updates, the user must edit before allowing to save changes      
        if 'pages_loaded' in global_state.get_key_names() and global_state['pages_loaded']:            
            st.switch_page(os.path.join('web_pages', 'general_product_and_manufacturer_information.py'))            
        else:
            streamlit_js_eval(js_expressions="parent.window.location.reload()")                    
    else:
        st.write('The product ID you have entered is not valid. Please try again')