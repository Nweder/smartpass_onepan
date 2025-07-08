import streamlit as st
import os
import lib
import global_state_lib as gsl

# Load the global state

st.set_page_config(page_title="Digital Product Passport", page_icon=":material/edit:", layout = 'wide')
global_state = gsl.get_global_state()


if 'company' in global_state.get_key_names():
    pages = []
    pages.append(st.Page("web_pages/product_id.py", title="Enter Product ID", icon=":material/verified_user:"))
    pages.append(st.Page("web_pages/select_company.py", title="Select Company", icon=":material/enterprise:"))
    #Get the name of the logo image
    #list files in the directory
    path_image = os.path.join(os.getcwd(),os.path.join("images", global_state['company']))
    files = [f for f in os.listdir(path_image) if os.path.isfile(os.path.join(path_image, f)) and 'logo'in str(f)]
    st.sidebar.image(os.path.join(path_image,files[0]), caption=global_state['company'])
    global_state['pages_loaded'] = False
else:
    pages = []
    pages.append(st.Page("web_pages/select_company.py", title="Select Company", icon=":material/enterprise:"))
    global_state['pages_loaded'] = False

#https://your_app.streamlit.app/?first_key=1&second_key=two&third_key=true
#http://172.25.113.104:8501/?Product_ID=2

if 'Product_ID' in st.query_params and not('request' in st.session_state.keys()):    
    st.session_state['request'] = False       
    product_id = st.query_params['Product_ID']
    fd = lib.communication()
    fd.fetch_data(product_id)

if global_state['status'] == 'OK':                   
    function_names = list(global_state['metadata_data_content_pages'][category]['function_name'] 
                          for category in global_state['metadata_data_content_pages'].keys())
    lib.create_generic_page_py(function_names)    
    i = 0
    pages = []
    for page in global_state['metadata_data_content_pages'].keys():
                  
        pages.append(st.Page('web_pages/'+function_names[i]+'.py', title=page, 
                            icon=global_state['metadata_data_content_pages'][page]['icon_category']))                  
        i = i + 1
    pages.append(st.Page("web_pages/user_login.py", title="User login", icon=":material/passkey:"))
    pages.append(st.Page("web_pages/product_id.py", title="Enter Product ID", icon=":material/verified_user:"))
    pages.append(st.Page("web_pages/select_company.py", title="Select Company", icon=":material/enterprise:"))
    global_state['pages_loaded'] = True

        
pg = st.navigation(pages)   
global_state['current_page_name'] = pg.title if pg.title != '' else 'Home'

pg.run()
    
        