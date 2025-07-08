:: Activates the environment
ECHO Activating Environment
CALL conda activate dpp_app
 
:: Run Web application
ECHO Running Web application
streamlit run src/main.py