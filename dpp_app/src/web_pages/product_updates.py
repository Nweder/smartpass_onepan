
import lib
import global_state_lib as gsl
# Load the global state
global_state = gsl.get_global_state()

    
metadata_content_pages = global_state['metadata_data_content_pages'][global_state['current_page_name']]
headers = metadata_content_pages['headers']
values = metadata_content_pages['values']
conf_print = metadata_content_pages['conf_print']
formats = metadata_content_pages['formats']
lib.print_data(headers, values, conf_print, formats)
    