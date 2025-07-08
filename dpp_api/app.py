import os
import pandas as pd
import yaml
import numpy as np
import re
import json
from flask import Flask, request, jsonify

app = Flask(__name__)
static_file = 'static.csv'
dynamic_file = 'dynamic.csv'

path_data = ''
parameter_metadata_file = ''

def main():
    app.run(debug=True)

#Request public datas
@app.route('/req_pub_data', methods=['GET'])
def req_pub_data():
    global path_data
    global parameter_metadata_file
    try:
        answer = {}
        #Get the product ID requested
        data = request.get_json(force=True)
        product_id = int(data['Product_ID'])
        company = str(data['company'])
        path_data = os.path.join('./data/', company)
        parameter_metadata_file = r'./data/'+company+'/parameter_metadata_'+company+'.xlsx' #THIS IS HARDCODED, I WILL CHANGE IT LATER
        answer['static'] = get_static_data(product_id)   
        answer['dynamic'] = get_dynamic_data(product_id)
        return jsonify(message=str(answer))
    except Exception as e:
        return jsonify(message=e.description)

def get_static_data(product_id, access='public'):    
    #Get the data for the product ID
    product_data = get_product_data(product_id, static_file, 'static', access)
    #Create the json data according to the data model definition
    json_data = data_model_definition(product_data, 'itemOffered', 'staticParameters_header.txt')
    return json_data    

def get_dynamic_data(product_id, access='public'):    
    #Get the data for the product ID
    product_data = get_product_data(product_id, dynamic_file, 'dynamic', access)
    #Create the json data according to the data model definition
    json_data = data_model_definition(product_data, 'Update', 'dynamicParameters_header.txt')
    return json_data  

def get_composed_parameters(df):
    list = []
    for index, row in df.iterrows():
        if row['subparameter'] != '':
            subparameters = re.findall(r'[A-Za-z]+', row['subparameter'])
            tmp_list = [row['parameter']+ '.'+ elem for elem in subparameters]
        else:
            tmp_list = [row['parameter']]
        list = list + tmp_list
    return list

def get_product_data(product_id, file, type, access='public'):
    #Access the product data
    product_df = pd.read_csv(os.path.join(path_data, file))
    #Access only the data for the product_id
    product_data_df = product_df[product_df['Product ID'] == product_id]    
    #Dont bring historic data if the access is public
    if access == 'public' and 'Historic' in product_data_df.columns:        
        product_data_df = product_data_df[product_data_df['Historic'] == 0]
        product_data_df.reset_index(drop=True, inplace=True)
    #Access the parameter metadata
    parameter_metadata_df = pd.read_excel(parameter_metadata_file, sheet_name='parameter_metadata')
    #lowercase type and access columns
    parameter_metadata_df['type'] = parameter_metadata_df['type'].apply(lambda row: row.lower())
    parameter_metadata_df['access'] = parameter_metadata_df['access'].apply(lambda row: row.lower())
    #Get parameters      
    if type == 'static':
        filter_static = parameter_metadata_df['type'] == type
    else:        
        filter_static = parameter_metadata_df['type'] == type
        #Add Product ID to the filter_static
        filter_static = np.logical_or(filter_static, parameter_metadata_df['parameter'] == 'Product ID')
    #replace NaN values with empty string
    parameter_metadata_df['subparameter'] = parameter_metadata_df['subparameter'].fillna('')    
    if access=='public':
        parameters = get_composed_parameters(parameter_metadata_df.loc[np.logical_and(filter_static, parameter_metadata_df['access'] == 'public'),['parameter','subparameter']])
    else:
        parameters = get_composed_parameters(parameter_metadata_df.loc[filter_static, ['parameter','subparameter']])
    #Get data
    product_public_data_df = product_data_df[parameters]
    return product_public_data_df

def parse_data(data):
    if isinstance(data, (int, np.int64)):
        return int(data)
    elif isinstance(data, (float, np.float64)):
        return float(data)
    elif isinstance(data, str):
        return str(data)
    else:
        return data
    
#Request public and private data
@app.route('/req_all_data', methods=['GET'])
def req_all_data():
    global path_data
    global parameter_metadata_file
    try:
        answer = {}
        #Get the product ID requested
        data = request.get_json(force=True)
        product_id = int(data['Product_ID'])
        company = str(data['company'])
        path_data = os.path.join('./data/', company)
        parameter_metadata_file = r'./data/'+company+'/parameter_metadata_'+company+'.xlsx' #THIS IS HARDCODED, I WILL CHANGE IT LATER
        answer['static'] = get_static_data(product_id, access='public_private')   
        answer['dynamic'] = get_dynamic_data(product_id, access='public_private')
        return jsonify(message=str(answer))
    except Exception as e:
        return jsonify(message=e.description)

def data_model_definition(product_data, type, file):
    #get definition of the data model
    #read json file
    data_model_definition_template = yaml.safe_load(open(os.path.join('./data/', 'data_model_definition',file)))
    #Access the parameter metadata
    parameter_metadata_df = pd.read_excel(parameter_metadata_file, sheet_name='parameter_metadata')
    #data to populate
    parameters = product_data.columns
    #Create json data with the data model definition    
    updates = []  
    for row in range(len(product_data)):
        copy_dmd = {}
        try:        
            for parameter in parameters:            
                if '.' in parameter: #Populate data when the parameter is nested
                    parent_parameter,sub_parameter = parameter.split('.')
                    sub_table_df = parameter_metadata_df[parameter_metadata_df['parameter']==parent_parameter]                   
                    if not(parent_parameter in dmd_dic): #is the dmd string already in cmpy_dmd?   
                        dmd_dic = json.loads(sub_table_df['data model definition string'].values[0])    
                    if 'value' in dmd_dic[parent_parameter][sub_parameter]['value']: #if the value is a dictionary                 
                        dmd_dic[parent_parameter][sub_parameter]['value']['value']['@value'] = parse_data(product_data[parameter].values[row])
                    else:
                        dmd_dic[parent_parameter][sub_parameter]['value']['@value'] = parse_data(product_data[parameter].values[row])
                    copy_dmd[parent_parameter] = dmd_dic[parent_parameter]             
                else: #Populate data when the parameter is explicit                         
                    sub_table_df = parameter_metadata_df[parameter_metadata_df['parameter']==parameter]
                    dmd_dic = json.loads(sub_table_df['data model definition string'].values[0])                 
                    if '@value' in dmd_dic[parameter]['value']: #if the value is a dictionary
                        dmd_dic[parameter]['value']['@value'] = parse_data(product_data[parameter].values[row])  
                    else: #The parameter is nested 
                        dmd_dic[parameter]['value']['value']['@value'] = parse_data(product_data[parameter].values[row])                             
                    copy_dmd[parameter] = dmd_dic[parameter]
        except:
            a=3
        if len(product_data) > 1:              
            updates.append(copy_dmd)
        else:
            updates = copy_dmd        
    data_model_definition_template[type] = updates
    return data_model_definition_template

def get_dynamic_product_data(product_id):
    #Access the product data
    update_product_df = pd.read_csv(os.path.join(path_data, dynamic_file))
    #Access only the data for the product_id
    update_product_df = update_product_df[update_product_df['Product ID'] == product_id]
    update_product_df.reset_index(drop=True, inplace=True)
    return update_product_df

#Post dynamic data
@app.route('/post_dynamic_data', methods=['POST'])
def post_dynamic_data():
    global path_data
    global parameter_metadata_file
    try:       
        #Get the product ID requested
        data = request.get_json(force=True)
        company = str(data['company'])
        path_data = os.path.join('./data/', company)
        parameter_metadata_file = r'./data/'+company+'/parameter_metadata_'+company+'.xlsx' #THIS IS HARDCODED, I WILL CHANGE IT LATER                
        _, data_df = parse_message(data)
        #Update dynamic database
        update_dynamic_database(data_df)
        return jsonify(message='{message: "Data posted"}')
    except Exception as e:
        return jsonify(message=e.description)

def update_dynamic_database(updated_data_df):
    #Access the product data
    product_df = pd.read_csv(os.path.join(path_data, dynamic_file))
    #Convert the data to string
    product_df['Product ID'] = product_df['Product ID'].astype(float).astype(int).astype(str)
    #Access only the data for the product_id
    product_id = updated_data_df['Product ID'].values[0]        
    #Remove old data for the product_id
    product_df = product_df[product_df['Product ID'] != str(product_id)]
    #Append new data
    product_df = pd.concat([product_df, updated_data_df], ignore_index=True)    
    #Sort by product ID and DPP Update Timestamp
    product_df = product_df.sort_values(by=['Product ID', 'DPP Update Timestamp'], ascending=[True,True])
    product_df.reset_index(drop=True, inplace=True)                                                                                              
    #Save the data
    product_df.to_csv(os.path.join(path_data, dynamic_file), index=False)

def parse_message(data):
    answer = json.loads(data['message'].replace("'","\""))    
    dmd_static_df = pd.DataFrame()
    dmd_dynamic_df = pd.DataFrame()
    #Access the parameter metadata
    parameter_metadata_df = pd.read_excel(parameter_metadata_file, sheet_name='parameter_metadata')
    for type_parameter in answer.keys():            
        if type_parameter == 'static':
            kind = 'itemOffered'
            parameters = list(answer[type_parameter]['itemOffered'].keys())
        elif type_parameter == 'dynamic':
            kind = 'Update'
            parameters = list(answer[type_parameter]['Update'][0].keys())        
        for parameter in parameters:
            if type_parameter == 'static':                
                string_value = answer[type_parameter][kind][parameter]
                value,format,raw_values = fetch_value(string_value)                                    
                dmd_static_df = save_values_in_df(parameter_metadata_df, dmd_static_df, parameter, raw_values,0)
            elif type_parameter == 'dynamic':
                values = []  
                formats = []                                                                     
                for i in range(len(answer[type_parameter][kind])):   
                    string_value = answer[type_parameter][kind][i][parameter]                     
                    value,format,raw_values = fetch_value(string_value)                        
                    values.append(value)  
                    formats.append(format)                        
                    dmd_dynamic_df = save_values_in_df(parameter_metadata_df, dmd_dynamic_df, parameter, raw_values, i)
    
    return dmd_static_df, dmd_dynamic_df                                                                       

def save_values_in_df(parameter_metadata_df, df, parameter, raw_values, row):
    if len(raw_values)==1:
        df.loc[row,parameter] = raw_values[0]
    else:
        for value in raw_values:
            subparameters_string = parameter_metadata_df.loc[parameter_metadata_df['parameter'] == parameter, 'subparameter']
            subparameters = subparameters_string.values[0][1:-1].split(',')
            #Remove blank spaces
            subparameters = [x.strip() for x in subparameters]
            for value, subparameter in zip(raw_values,subparameters):
                df.loc[row,parameter+'.'+subparameter] = value
    return df   

def fetch_value(data_dic):
    raw_values = []
    try:
        if 'value' in data_dic.keys():
            if '@value' in data_dic['value'].keys():
                value = data_dic['value']['@value']
                format = data_dic['value']['@type']
                raw_values.append(value)
                if 'unitCode' in data_dic['value'].keys():
                    units = data_dic['value']['unitCode']
                    value = str(value) + ' ' + units
            else:
                value = data_dic['value']['value']['@value']
                format = data_dic['value']['value']['@type']
                raw_values.append(value)
                if 'unitCode' in data_dic['value']['value'].keys():
                    units = data_dic['value']['value']['unitCode']
                    value = str(value) + ' ' + units                
        elif '@value' in data_dic.keys():
            value = data_dic['@value']
            format = data_dic['@type']
            raw_values.append(value)
            if 'unitCode' in data_dic.keys():
                units = data_dic['unitCode']
                value = str(value) + ' ' + units                
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
                            value = str(value) + ' ' + units
                    else:
                        value = data_dic[key]['value']['value']['@value']
                        format = data_dic[key]['value']['value']['@type']
                        raw_values.append(value)
                        if 'unitCode' in data_dic[key]['value']['value'].keys():
                            units = data_dic[key]['value']['value']['unitCode']
                            value = str(value) + ' ' + units
                    value_arr.append(value)
                    format_arr.append(format)
            value = ', '.join(value_arr)
            format = ', '.join(format_arr)
    except:
        value = ''
    return value, format, raw_values
if __name__ == '__main__':
    main()