import socket
import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import os
import global_state_lib as gsl
import yaml
import qrcode

from yaml.loader import SafeLoader
from datetime import datetime
from PIL import Image
import time

url = "http://backend:5000/"
#url = "http://127.0.0.1:5000/"
company = 'ONEPan'

units_file = 'data/units.xlsx'
units_dict = {}
#open dataframe
units_df = pd.read_excel(os.path.join(os.getcwd(), units_file))
#Convert to dictionary
for index, row in units_df.iterrows():
    units_dict[row['Common Code']] = row['Symbol']

header_color = f''':gray'''

header = '''
import lib
import global_state_lib as gsl
# Load the global state
global_state = gsl.get_global_state()

    '''
body_src = '''
metadata_content_pages = global_state['metadata_data_content_pages'][global_state['current_page_name']]
headers = metadata_content_pages['headers']
values = metadata_content_pages['values']
conf_print = metadata_content_pages['conf_print']
formats = metadata_content_pages['formats']
lib.print_data(headers, values, conf_print, formats)
    ''' 
with open('src/credentials.yml') as file:
    config = yaml.load(file, Loader=SafeLoader)

@st.dialog("Edit Authentication", width="large")
def user_edit_authentication(global_state):
    economic_operator = st.text_input("DPP Update Responsible")
    password = st.text_input("Password", type="password")
    col1, col2 = st.columns([1,8])
    with col1:
        submit = st.button('Login')
    with col2:
        cancel = st.button('Cancel') 
    st.markdown(':blue[You can test with the DPP Update Responsible] :' )
    st.markdown(':blue[ONEPan]')
    st.markdown(':blue[Password for all is abc]')
    st.markdown(':blue[(Watch out with lower and uppercase)]')    

    if submit:        
        if economic_operator in config['credentials']['edit_user_authentication'].keys():            
            psw = config['credentials']['edit_user_authentication'][economic_operator]['password']
            if password == psw : #login successful
                global_state['user_edit_authentication'] = economic_operator
                st.rerun()
            else:
                global_state['user_edit_authentication'] = None
                st.error('Password is incorrect')
        else:
            global_state['user_edit_authentication'] = None
            st.error('DPP Update Responsible is incorrect')
    if cancel:
        global_state['user_edit_authentication'] = None
        st.rerun()

def insert_updated_row(global_state, index, tmp_df, historic, update_id=""):
    #Append the inserted row
    global_state['df_update'] = pd.concat([global_state['df_update'], pd.DataFrame(index=[0],data=tmp_df.loc[index].to_dict())], ignore_index=True)
    #Add DPP Update Timestamp with the current time
    global_state['df_update'].loc[index, 'DPP Update Timestamp'] = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    #Add DPP Update Responsible
    global_state['df_update'].loc[index, 'DPP Update Responsible'] = global_state['user_edit_authentication']
    #Add Product ID
    global_state['df_update'].loc[index, 'Product ID'] = global_state['product_id']
    #Add Historic
    global_state['df_update'].loc[index, 'Historic'] = historic
    #Add Update ID
    if historic:
        global_state['df_update'].loc[index, 'Update ID'] = update_id
    else:
        global_state['df_update'].loc[index, 'Update ID'] = get_new_update_id(global_state)

def get_new_update_id(global_state):
    if len(global_state['df_update'])==0:
        last_update_id = 1
    else:
        #Change datatype to float    
        global_state['df_update']['Update ID'] = pd.to_numeric(global_state['df_update']['Update ID'])
        #Sort the dataframe by Update ID
        global_state['df_update'] = global_state['df_update'].sort_values(by='Update ID')
        global_state['df_update'].reset_index(drop=True, inplace=True)
        #Get the last Update ID
        last_update_id = global_state['df_update']['Update ID'].tail(1).values[0]
    return last_update_id + 0.1

def add_row(global_state, formats):
    dic_new = {'Update ID':get_new_update_id(global_state), 
               'DPP Update Responsible':global_state['user_edit_authentication'], 
               'Product ID':global_state['product_id'], 
               'Historic':0, 
               'DPP Update Timestamp':str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}
    #For all columns not in the dictory, add empty values according to the formats
    for col in global_state['df_update'].columns:
        #get index of col in global_state['df_update'].columns
        index = global_state['df_update'].columns.get_loc(col)
        if col not in dic_new.keys():
            if formats[index] == 'xsd:string' or formats[index] == 'xsd:anyURI' or formats[index] == 'gs1:pip':
                dic_new[col] = '-'
            elif formats[index] == 'xsd:integer':
                dic_new[col] = 0
            elif formats[index] == 'xsd:float':
                dic_new[col] = 0.0
            elif formats[index] == 'xsd:boolean':
                dic_new[col] = 0
            elif formats[index] == 'xsd:dateTime':
                dic_new[col] = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))           
    #Add row
    global_state['df_update'] = pd.concat([global_state['df_update'], pd.DataFrame(index=[0],data=dic_new)], ignore_index=True)    
    

#@st.dialog("Add product Update", width="large")
def edit_update(values, header, global_state, formats, show_historic_updates=False):
    if 'user_edit_authentication' not in global_state.get_key_names() or global_state['user_edit_authentication']==None:
        user_edit_authentication(global_state)
    else:
        if not('df_update' in global_state.get_key_names()) or global_state['df_update'] is None:
            #Filter the data only with the rows of the DPP Update Responsible and no historic updates
            dpp_update_responsible = global_state['user_edit_authentication'] 
            filter = np.logical_and(values[header]['DPP Update Responsible'] == dpp_update_responsible, values[header]['Historic']==False)                                                           
            global_state['df_update'] = pd.DataFrame(pd.DataFrame.to_dict(values[header].loc[filter]))
            global_state['df_update'].reset_index(drop=True, inplace=True)
            global_state['no_df_update'] = len(global_state['df_update'])
            #global_state['df_update_new_rows'] = pd.DataFrame()
            #This line is not necesary if the product_id is a string
            global_state['df_update']['Product ID'] = global_state['product_id']
            #global_state['df_update'].reset_index(drop=True, inplace=True)            
            df = pd.DataFrame([{"command": "st.selectbox", "rating": 4, "is_widget": True},{"command": "st.balloons", "rating": 5, "is_widget": False},{"command": "st.time_input", "rating": 3, "is_widget": True},])
        st.markdown("""---""")
        st.markdown("""### Edit Update""")
        add_row_button = st.button("Add row")
        if add_row_button:
            add_row(global_state, formats[header])
        disabled_columns = ['Product ID', 'DPP Update Responsible','Update ID', 'DPP Update Timestamp', 'Historic']
        tmp_df = st.data_editor(global_state['df_update'], disabled=disabled_columns)
        col1, col2 = st.columns([1,10])
        with col1:
            save = st.button('Save')
        with col2:
            cancel = st.button('Cancel')
        if save:                       
            #This line is not necesary if the product_id is a string
            tmp_df['Product ID'] = global_state['product_id']
            for index in range(len(tmp_df)):                                
                if index>=global_state['no_df_update']: #It is a new row   
                    for col in tmp_df.columns:
                        if col not in ['Update ID', 'DPP Update Responsible', 'Product ID', 'Historic', 'DPP Update Timestamp']: #Exclude columns
                            global_state['df_update'].loc[index, col] = tmp_df.loc[index, col]
                    global_state['save_changes'] = True
                    break
                # Verify for changes in each column
                for column in tmp_df.columns:
                    if tmp_df.loc[index, column] != global_state['df_update'].loc[index, column]:
                        #Change the status of the updated row to historic                        
                        tmp_df.loc[index, 'Historic'] = 0
                        insert_updated_row(global_state, index, tmp_df, 1, tmp_df.loc[index,'Update ID'])
                        global_state['save_changes'] = True
                        break                                 
            #Keep rows with a different DPP Update Responsible or historic updates
            filter = np.logical_or(global_state['metadata_data_content_pages']
                                   [global_state['current_page_name']]['values']
                                   [header]['DPP Update Responsible'] != global_state['user_edit_authentication'], 
                                   global_state['metadata_data_content_pages'][global_state['current_page_name']]
                                   ['values'][header]['Historic']==1)
            global_state['metadata_data_content_pages'][global_state['current_page_name']]['values'][header] = global_state['metadata_data_content_pages'][global_state['current_page_name']]['values'][header].loc[filter]            
            #Append the new rows
            global_state['metadata_data_content_pages'][global_state['current_page_name']]['values'][header] = pd.concat([global_state['metadata_data_content_pages'][global_state['current_page_name']]['values'][header], global_state['df_update']], ignore_index=True) 
            #This line is not necesary if the product_id is a string
            global_state['metadata_data_content_pages'][global_state['current_page_name']]['values'][header]['Product ID'] = global_state['product_id']
            global_state['df_update'] = None
            global_state['user_edit_authentication'] = None
            st.rerun()
        if cancel:
            global_state['df_update'] = None
            global_state['user_edit_authentication'] = None
            st.rerun()

def print_data (headers, values, conf_print, formats, header_color=header_color):
    #Embed the data model definition in the web page
    global_state = gsl.get_global_state()
    if conf_print[list(headers.keys())[0]] == 'table':
        st.markdown("""<script type="application/ld+json">{}</script>""".format(global_state['dmd_Update']), unsafe_allow_html=True)
    else:
        st.markdown("""<script type="application/ld+json">{}</script>""".format(global_state['dmd_itemOffered']), unsafe_allow_html=True)
    for header in headers.keys():
        st.header(header)
        st.markdown("""---""")
        if conf_print[header] != 'table':
            col1, col2 = st.columns(2, gap='small')
            cols = [col1, col2]
        cc = 0
        for i in range(len(headers[header])):
            if conf_print[header] == 'table':
                #Order by Update ID                
                values[header] = values[header].sort_values(by='Product ID')                
                values[header].reset_index(drop=True, inplace=True) 
                #Create config for the columns
                column_config = {}
                # If the dataframe contains a CO2 saving column, show a prominent metric above the table
                try:
                    df_table = values[header]
                    # Look for likely CO2 saving column names (case-insensitive)
                    co2_cols = [c for c in df_table.columns if ('co2' in c.lower() and 'save' in c.lower()) or 'co2 saving' in c.lower()]
                    if not co2_cols:
                        # fallback: column contains both 'co2' and 'saving' words separately
                        co2_cols = [c for c in df_table.columns if 'co2' in c.lower() and 'saving' in c.lower()]
                    if co2_cols:
                        co2_col = co2_cols[0]
                        # prefer non-historic rows if Historic column exists
                        if 'Historic' in df_table.columns:
                            df_non_hist = df_table[df_table['Historic'] == False]
                        else:
                            df_non_hist = df_table
                        if len(df_non_hist) == 0:
                            df_non_hist = df_table
                        # Try to get the last available numeric value
                        try:
                            candidate_vals = df_non_hist[co2_col].dropna().values
                            if len(candidate_vals) > 0:
                                last_val = candidate_vals[-1]
                                # convert to float if possible
                                try:
                                    val_num = float(last_val)
                                    # Show metric with two decimals and unit
                                    st.metric(label="CO₂ saved", value=f"{val_num:,.2f}", delta="kg CO₂-eq")
                                except Exception:
                                    # If it's not numeric, just print as-is
                                    st.markdown(f"#### CO₂ saved: **{last_val}**")
                        except Exception:
                            pass
                except Exception:
                    pass
                for i in range(len(values[header].columns)):
                    if formats[header][i] == 'xsd:anyURI' or formats[header][i] == 'gs1:pip' or (formats[header][i] == 'xsd:string' and isinstance(values[header][values[header].columns[i]].values[0], str) and len(values[header][values[header].columns[i]].values[0])>4 and 'http'==values[header][values[header].columns[i]].values[0][0:4]):
                        column_config[values[header].columns[i]] = st.column_config.LinkColumn(values[header].columns[i])
                if 'Login' in global_state.get_key_names() and global_state['Login']: #If the user did login, allow edit mode  
                    if 'user_edit_authentication' not in global_state.get_key_names() or global_state['user_edit_authentication'] is None :
                        if 'Historic' in values[header].columns:
                            global_state['show_historic_updates'] = st.checkbox('Show all including historic updates')
                        else:
                            global_state['show_historic_updates'] = False
                        col_btn1, col_btn2 = st.columns([1,8])
                        col_btn = [col_btn1, col_btn2]
                        if 'save_changes' in global_state.get_key_names() and global_state['save_changes']:                            
                            if col_btn[1].button('Write data in database'):
                                fd = communication()
                                status = fd.send_data(global_state['metadata_data_content_pages'][global_state['current_page_name']]['values'][header])
                                if status == 'OK':
                                    global_state['save_changes'] = False
                                    global_state['save_changes_success'] = True
                                    st.rerun()
                                else:
                                    st.error('Error in writing data in data base')
                        if col_btn[0].button('Add/Edit update'):
                            edit_update(values, header, global_state, formats, global_state['show_historic_updates'])
                        else:
                            if global_state['show_historic_updates']:
                                filter = values[header].index
                            else:
                                filter = values[header]['Historic']==global_state['show_historic_updates']   
                            st.dataframe(values[header].loc[filter], column_config=column_config)
                    else:               
                        edit_update(values, header, global_state, formats, global_state['show_historic_updates'])
                else:
                    if 'show_historic_updates' in global_state.get_key_names() and global_state['show_historic_updates']:
                        #show historic updates 
                        filter = values[header].index
                    else:
                        if 'Historic' in values[header].columns:
                            filter = values[header]['Historic']==False
                        else:
                            filter = values[header].index   
                    st.dataframe(values[header].loc[filter], column_config=column_config) 
                if 'save_changes_success' in global_state.get_key_names() and global_state['save_changes_success']:
                    st.success('Data saved successfully')
                    global_state['save_changes_success'] = False                   
                break
            else:
                cols[cc].markdown('''##### ''' + header_color + '''[''' + headers[header][i]+": " + ''']''')
                if formats[header][i]=='xsd:anyURI' or formats[header][i]=='gs1:pip' or (formats[header][i] == 'xsd:string' and isinstance(values[header][i], str) and len(values[header][i])>4 and 'http'==values[header][i][0:4]):
                    cols[cc].markdown('''#### ''' + '''[''' + 'More Information' + '''](''' + str(values[header][i]) + ''')''')
                else:
                    # Check if this parameter looks like a CO2-saving parameter and print in Swedish
                    try:
                        header_name = headers[header][i]
                        value_to_print = values[header][i]
                        header_check = header_name.lower()
                    except Exception:
                        header_check = ''
                        value_to_print = values[header][i]

                    # If the parameter name indicates CO2 saving, show a more friendly Swedish message
                    if 'co2 saving' in header_check or ('co2' in header_check and 'saving' in header_check):
                        # English phrasing for CO2 saving
                        cols[cc].markdown('''#### CO2 saved is ''' + str(value_to_print))
                    else:
                        cols[cc].markdown('''#### ''' + str(value_to_print))
            if i == int(len(headers[header])/2)-1:
                cc = 1
        st.markdown("""---""")

class communication:    

    def __init__(self):
        # Load the global state
        self.global_state = gsl.get_global_state()
        parameter_metadata_file = self.global_state['company']+'/parameter_metadata_'+self.global_state['company']+'.xlsx'
        #read paramater_metadata.xlsx        
        self.parameter_metadata_df = pd.read_excel(os.path.join(os.getcwd(), os.path.join('data',parameter_metadata_file)), sheet_name='parameter_metadata')
        #Order by order_parameter
        self.parameter_metadata_df = self.parameter_metadata_df.sort_values(by='order_parameter')        
        self.category_metadata_df = pd.read_excel(os.path.join(os.getcwd(), os.path.join('data',parameter_metadata_file)), sheet_name='category_metadata')
        self.sub_category_metadata_df = pd.read_excel(os.path.join(os.getcwd(), os.path.join('data',parameter_metadata_file)), sheet_name='sub_category_metadata')

    def send_data(self, product_data):
        global url
        global url_alt
        body_dynamic = {}
        self.api_send_url = url + "post_dynamic_data"  
        #self.api_send_url_alt = url_alt + "post_dynamic_data"  
        body = self.data_model_definition(product_data, 'Update', 'dynamicParameters_header.txt')
        body_dynamic['dynamic'] = body
        body_str = "{\"company\":\"" + self.global_state['company'] + "\", \"message\":\"" + str(body_dynamic) + "\"}"
        status = self.api_send(body_str.encode('ascii'))  
        return status

    def api_send(self, body):
        with st.spinner("Working..."):
            accept_json={'Content-Type': 'application/json', 'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br'}
            ### invoke API and post the response
            response = requests.post(url=self.api_send_url, headers=accept_json , data=body)
            #response_alt = requests.post(url=self.api_send_url_alt, headers=accept_json , data=body)
            #if response_alt.status_code == requests.codes.ok:
            #    response = response_alt
            if response.status_code == requests.codes.ok:                
                status = "OK"
            else:
                data = {"code": response.status_code, "message": response.text}
                metadata_data_content_pages = {}
                status = "ERROR"
        return status    
    
    def fetch_data(self, product_id):
        global url
        global url_alt
        self.global_state['product_id'] = product_id  
        if 'Login' in self.global_state.get_key_names() and self.global_state['Login']: #If the user did login, load private data
            access = 'private'
        else:
            access = 'public'
        #Lower case access
        self.parameter_metadata_df['access'] = self.parameter_metadata_df['access'].str.lower()
        #filter the data based on access        
        if access=='public':
            self.parameter_metadata_df = self.parameter_metadata_df[self.parameter_metadata_df['access'] == 'public']
            self.parameter_metadata_df.reset_index(drop=True, inplace=True)
            self.api_url = url+"req_pub_data"
            #self.api_url_alt = url_alt+"req_pub_data"
        else:
            self.api_url = url+"req_all_data"
            #self.api_url_alt = url_alt+"req_all_data"
        product_id_str = "{\"company\":\"" + str(self.global_state['company']) + "\", \"Product_ID\":\"" + str(product_id) + "\"}"
        self.global_state['status'], self.global_state['metadata_data_content_pages'] = self.api_request(product_id_str.encode('ascii'))

    def create_metadata_content_pages(self):
        dic = {}        
        for category in self.parameter_metadata_df['category'].unique():            
            dic[category] = {}
            dic[category]['icon_category'] = self.category_metadata_df.loc[self.category_metadata_df['category'] == category, 'icon_category'].values[0]
            dic[category]['function_name'] = self.category_metadata_df.loc[self.category_metadata_df['category'] == category, 'function_name'].values[0]
            filter_df = self.parameter_metadata_df[self.parameter_metadata_df['category'] == category]
            dic[category]['headers'] = {}
            dic[category]['conf_print'] = {}
            dic[category]['values'] = {}
            dic[category]['formats'] = {}
            for sub_category in filter_df['sub_category'].unique():
                dic[category][sub_category] = {}
                filter2_df = filter_df[filter_df['sub_category'] == sub_category]
                dic[category]['headers'][sub_category] = filter2_df['parameter'].tolist()                                
                dic[category]['conf_print'][sub_category] = self.sub_category_metadata_df.loc[self.sub_category_metadata_df['sub_category'] == sub_category, 'conf_print'].values[0]
                if dic[category]['conf_print'][sub_category] == 'strings':
                    dic[category]['values'][sub_category] = filter2_df['value'].tolist()
                    dic[category]['formats'][sub_category] = filter2_df['format'].tolist()
                elif dic[category]['conf_print'][sub_category] == 'table':
                    dic[category]['values'][sub_category] = self.dmd_dynamic_df
                    #Include product_id in filter2_df
                    filter_df = self.parameter_metadata_df[np.logical_or(self.parameter_metadata_df['category'] == category, self.parameter_metadata_df['parameter'] == 'Product ID')]  
                    filter2_df = filter_df[np.logical_or(filter_df['sub_category'] == sub_category, filter_df['parameter'] == 'Product ID')]
                    tmp_list = [elem.split(', ') for elem in filter2_df['format'].tolist()]     
                    dic[category]['formats'][sub_category] = [item for sublist in tmp_list for item in sublist]
        return dic

    def parameter_metadata(self):
        return self.parameter_metadata
    
    def category_metadata(self):
        return self.category_metadata_df
    
    def sub_category_metadata(self):
        return self.sub_category_metadata_df
 
    def api_request(self, body):
        with st.spinner("Working..."):
            accept_json = {'Content-Type': 'application/json', 'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br'}
            ### invoke API and get the response with retries for transient network/DNS failures
            max_retries = 5
            backoff_base = 0.5
            response = None
            last_exc = None
            for attempt in range(max_retries):
                try:
                    response = requests.get(url=self.api_url, headers=accept_json, data=body, timeout=5)
                    break
                except requests.exceptions.RequestException as e:
                    # Keep the exception and retry after exponential backoff
                    last_exc = e
                    if attempt < max_retries - 1:
                        time.sleep(backoff_base * (2 ** attempt))
                        continue
                    else:
                        response = None
            if response is not None and response.status_code == requests.codes.ok:
                ### Convert data to JSON format
                data = response.json()
                ### Now parse the data to dataframes
                self.parse_data(data)
                dmd_itemOffered = self.data_model_definition(self.dmd_static_df, 'itemOffered', 'staticParameters_header.txt')
                dmd_Update = self.data_model_definition(self.dmd_dynamic_df, 'Update', 'dynamicParameters_header.txt')
                self.global_state['dmd_itemOffered'] = json.dumps(dmd_itemOffered)
                self.global_state['dmd_Update'] = json.dumps(dmd_Update)
                metadata_data_content_pages = self.create_metadata_content_pages()
                status = "OK"
            else:
                # If we have a response but a non-OK status, include response info; otherwise include exception message
                if response is not None:
                    data = {"code": response.status_code, "message": response.text}
                else:
                    data = {"code": -1, "message": str(last_exc)}
                metadata_data_content_pages = {}
                status = "ERROR"
        return status, metadata_data_content_pages

    def save_values_in_df(self, df, parameter, raw_values, row):
        if len(raw_values)==1:
            df.loc[row,parameter] = raw_values[0]
        else:
            for value in raw_values:
                subparameters_string = self.parameter_metadata_df.loc[self.parameter_metadata_df['parameter'] == parameter, 'subparameter']
                subparameters = subparameters_string.values[0][1:-1].split(',')
                #Remove blank spaces
                subparameters = [x.strip() for x in subparameters]
                for value, subparameter in zip(raw_values,subparameters):
                    df.loc[row,parameter+'.'+subparameter] = value                    

    def fetch_value(self, data_dic):
        raw_values = []
        try:
            if 'value' in data_dic.keys():
                if '@value' in data_dic['value'].keys():
                    value = data_dic['value']['@value']
                    format = data_dic['value']['@type']
                    raw_values.append(value)
                    if 'unitCode' in data_dic['value'].keys():
                        units = data_dic['value']['unitCode']
                        value = str(value) + ' ' + units_dict[units]
                else:
                    value = data_dic['value']['value']['@value']
                    format = data_dic['value']['value']['@type']
                    raw_values.append(value)
                    if 'unitCode' in data_dic['value']['value'].keys():
                        units = data_dic['value']['value']['unitCode']
                        value = str(value) + ' ' + units_dict[units]                
            elif '@value' in data_dic.keys():
                value = data_dic['@value']
                format = data_dic['@type']
                raw_values.append(value)
                if 'unitCode' in data_dic.keys():
                    units = data_dic['unitCode']
                    value = str(value) + ' ' + units_dict[units]                
            else: #It is a composed parameter
                value_arr = []
                format_arr = []                
                for key in data_dic.keys():                    
                    if key != '@type':
                        if '@value' in data_dic[key]['value'].keys():
                            value = data_dic[key]['value']['@value']
                            format = data_dic[key]['value']['@type']
                            raw_values.append(value)
                            if 'unitCode' in data_dic[key]['value'].keys():
                                units = data_dic[key]['value']['unitCode']
                                value = str(value) + ' ' + units_dict[units]
                        else:
                            value = data_dic[key]['value']['value']['@value']
                            format = data_dic[key]['value']['value']['@type']
                            raw_values.append(value)
                            if 'unitCode' in data_dic[key]['value']['value'].keys():
                                units = data_dic[key]['value']['value']['unitCode']
                                value = str(value) + ' ' + units_dict[units]
                        value_arr.append(value)
                        format_arr.append(format)
                value = ', '.join(value_arr)
                format = ', '.join(format_arr)
        except:
            value = ''
        return value, format, raw_values

    def parse_data(self, data):
        answer = json.loads(data['message'].replace("'","\""))
        self.parameter_metadata_df['value'] = ''
        self.dmd_static_df = pd.DataFrame()
        self.dmd_dynamic_df = pd.DataFrame()
        for type_parameter in answer.keys():            
            if type_parameter == 'static':
                kind = 'itemOffered'
                parameters = list(answer[type_parameter]['itemOffered'].keys())
            elif type_parameter == 'dynamic':
                kind = 'Update'
                if type(answer[type_parameter]['Update'])==dict:
                    parameters = list(answer[type_parameter]['Update'].keys())
                else:
                    parameters = list(answer[type_parameter]['Update'][0].keys())
            if type_parameter == 'dynamic':
                if type(answer[type_parameter][kind])==dict:
                    self.dynamic_df = pd.DataFrame(columns=list(answer[type_parameter][kind].keys()))
                else:
                    self.dynamic_df = pd.DataFrame(columns=list(answer[type_parameter][kind][0].keys()))
            for parameter in parameters:
                if type_parameter == 'static':                
                    string_value = answer[type_parameter][kind][parameter]
                    value,format,raw_values = self.fetch_value(string_value)                    
                    self.parameter_metadata_df.loc[self.parameter_metadata_df['parameter'] == parameter, 'value'] = value
                    self.parameter_metadata_df.loc[self.parameter_metadata_df['parameter'] == parameter, 'format'] = format
                    self.save_values_in_df(self.dmd_static_df, parameter, raw_values,0)
                elif type_parameter == 'dynamic':
                    values = []  
                    formats = []                                                                                         
                    if type(answer[type_parameter][kind])==dict:
                        string_value = answer[type_parameter][kind][parameter]
                        value,format,raw_values = self.fetch_value(string_value)                        
                        values.append(value)  
                        formats.append(format)                        
                        self.save_values_in_df(self.dmd_dynamic_df, parameter, raw_values, 0)
                    else:
                        for i in range(len(answer[type_parameter][kind])):   
                            string_value = answer[type_parameter][kind][i][parameter]                     
                            value,format,raw_values = self.fetch_value(string_value)                        
                            values.append(value)  
                            formats.append(format)                        
                            self.save_values_in_df(self.dmd_dynamic_df, parameter, raw_values, i)                                         
                    self.dynamic_df[parameter] = values
                    self.parameter_metadata_df.loc[self.parameter_metadata_df['parameter'] == parameter, 'format'] = formats[0]                     
    
    def parse_data_dmd(self, data):
        if isinstance(data, (int, np.int64)):
            return int(data)
        elif isinstance(data, (float, np.float64)):
            return float(data)
        elif isinstance(data, str):
            return str(data)
        else:
            return data
    
    def data_model_definition(self, product_data, type, file):
        #get definition of the data model
        #read json file
        data_model_definition_template = yaml.safe_load(open(os.path.join(os.getcwd(), 'data/data_model_definition',file)))
        #data to populate
        parameters = product_data.columns
        #Create json data with the data model definition    
        updates = []          
        for row in range(len(product_data)):
            copy_dmd = {}
            for parameter in parameters:             
                if '.' in parameter: #Populate data when the parameter is nested
                    parent_parameter,sub_parameter = parameter.split('.')
                    sub_table_df = self.parameter_metadata_df[self.parameter_metadata_df['parameter']==parent_parameter]                   
                    if not(parent_parameter in dmd_dic): #is the dmd string already in cmpy_dmd?   
                        dmd_dic = json.loads(sub_table_df['data model definition string'].values[0])    
                    if 'value' in dmd_dic[parent_parameter][sub_parameter]['value']: #if the value is a dictionary                 
                        dmd_dic[parent_parameter][sub_parameter]['value']['value']['@value'] = self.parse_data_dmd(product_data[parameter].values[row])
                    else:
                        dmd_dic[parent_parameter][sub_parameter]['value']['@value'] = self.parse_data_dmd(product_data[parameter].values[row])
                    copy_dmd[parent_parameter] = dmd_dic[parent_parameter]             
                else: #Populate data when the parameter is explicit                                                               
                    sub_table_df = self.parameter_metadata_df[self.parameter_metadata_df['parameter']==parameter]
                    try:
                        dmd_dic = json.loads(sub_table_df['data model definition string'].values[0]) 
                    except:
                        a =4
                    if '@value' in dmd_dic[parameter]['value']: #if the value is a dictionary                   
                        dmd_dic[parameter]['value']['@value'] = self.parse_data_dmd(product_data[parameter].values[row])
                    else:#The parameter is nested 
                        dmd_dic[parameter]['value']['value']['@value'] = self.parse_data_dmd(product_data[parameter].values[row])                                                 
                    copy_dmd[parameter] = dmd_dic[parameter]
            if len(product_data) > 1:              
                updates.append(copy_dmd)
            else:
                updates = copy_dmd
        data_model_definition_template[type] = updates
        return data_model_definition_template


def create_generic_page_py(page_names):    
    #Delete all page files in the folder pages
    if os.path.exists(os.path.join(os.getcwd(), 'src/web_pages')):        
        for file in os.listdir(os.path.join(os.getcwd(), 'src/web_pages')):
            # Preserve special pages that should not be auto-deleted
            if file in ('product_id.py', 'user_login.py', 'select_company.py', '__init__.py', 'home.py', 'saved_co2.py'):
                continue
            os.remove(os.path.join(os.getcwd(), 'src/web_pages/'+file))            
    #Create page files
    for page in page_names:
        body = ''
        body = body + body_src.replace('generic_page', page)
        with open(os.path.join(os.getcwd(), 'src/web_pages/'+page+'.py'), 'w') as f:
            f.write(header)
            f.write(body)
    #with open(os.path.join(os.getcwd(), 'src/generic_page.py'), 'w') as f:
    #    f.write(header)
    #    f.write(body)      

def get_ip():
    """
    Gets the host IP address in a way that works both inside and outside a Docker container.
    
    1. It first checks for the 'HOST_IP' environment variable, which is the
       recommended way to pass the host's IP to a Docker container.
       
    2. If the variable is not found (e.g., when running directly in Visual Studio),
       it falls back to a socket-based method to find the local IP.
       
    3. If all else fails, it returns '127.0.0.1'.
    """
    # Priority 1: Check for the environment variable (Docker method)
    host_ip = os.getenv('HOST_IP')
    if host_ip:
        return host_ip
        
    # Priority 2: Fallback for local execution (Visual Studio method)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        # Doesn't have to be reachable
        s.connect(('10.254.254.254', 1))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = '127.0.0.1' # Final fallback
    finally:
        s.close()
        
    return local_ip

def create_qr(path_data, file_name_logo, data, qr_name):    

    # Create a QR code object
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
   
    # Add the data to the QR code object
    qr.add_data(data)

    # Make the QR code
    qr.make(fit=True)

    # Create an image from the QR code
    img = qr.make_image(fill_color="black", back_color="white")

    # Open the logo or image file
    logo = Image.open(os.path.join(path_data, file_name_logo))

    # Resize the logo or image if needed
    logo = logo.resize((50, 50))

    # Position the logo or image in the center of the QR code
    img_w, img_h = img.size
    logo_w, logo_h = logo.size
    pos = ((img_w - logo_w) // 2, (img_h - logo_h) // 2)

    # Paste the logo or image onto the QR code
    img.paste(logo, pos)

    # Save the QR code image with logo or image
    img.save(os.path.join(path_data,qr_name))       