import streamlit as st
import os
import global_state_lib as gsl

# Load the global state
global_state = gsl.get_global_state()

st.title('Welcome to the Digital Product Passport')
st.markdown('''Please select the company you want to work with''')
columns = st.columns([1,1,1,1], vertical_alignment="bottom")
#list of companies in images folder

list_companies = [f for f in os.listdir(os.path.join(os.getcwd(), 'images')) if os.path.isdir(os.path.join(os.getcwd(), 'images', f))]
for company in list_companies:
    #Get the name of the logo image
    #list files in the directory
    path_image = os.path.join(os.getcwd(),os.path.join("images", company))
    files = [f for f in os.listdir(path_image) if os.path.isfile(os.path.join(path_image, f)) and 'logo'in str(f)] 
    if len(files) > 0:
        with columns[list_companies.index(company)].container():
            st.image(os.path.join(path_image,files[0]), caption=company, width=200)
            if st.button(company):
                global_state['company'] = company
                st.experimental_rerun()