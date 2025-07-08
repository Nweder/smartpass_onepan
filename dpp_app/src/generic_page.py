
import lib
import global_state_lib as gsl
# Load the global state
global_state = gsl.get_global_state()

    
def general_product_and_manufacturer_information():
    metadata_content_pages = global_state['metadata_data_content_pages'][global_state['current_page_name']]
    headers = metadata_content_pages['headers']
    values = metadata_content_pages['values']
    conf_print = metadata_content_pages['conf_print']
    lib.print_data(headers, values, conf_print)
    
    
def circularity_and_resource_efficiency():
    metadata_content_pages = global_state['metadata_data_content_pages'][global_state['current_page_name']]
    headers = metadata_content_pages['headers']
    values = metadata_content_pages['values']
    conf_print = metadata_content_pages['conf_print']
    lib.print_data(headers, values, conf_print)
    
    
def material_and_composition():
    metadata_content_pages = global_state['metadata_data_content_pages'][global_state['current_page_name']]
    headers = metadata_content_pages['headers']
    values = metadata_content_pages['values']
    conf_print = metadata_content_pages['conf_print']
    lib.print_data(headers, values, conf_print)
    
    