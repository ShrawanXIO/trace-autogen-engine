# 1. Create the virtual environment (Isolated Sandbox)
python -m venv .venv

# 2. Activate it (Windows)
venv\Scripts\activate
# OR Activate it (Mac/Linux)
# source venv/bin/activate

# 3. Install the libraries
pip install -r requirements.txt    
                                # Whatever the Dependencies that are required to run this project will be inside the requirements.txt file. 

# 4. run the app !! 

streamlit run src/app.py


##And sometimes we will not be able to discover our Python tests. So in order to discover the Python tests, we need to do this 
Press Ctrl+Shift+P.
Type Python: Configure Tests.
select Tests folder 
Must start with `test_`
