# KanyeToThe-Post-Deleter


# About
A Python script for mass-deleting all (deletable) posts from your account. Non-deletable posts will have their titles and OP message overwritten. 


Status: The basic functionality should be working currently, but it still needs additional testing. Add your user credentials in the "login_payload" variable in the login() function before running. Currently has a high time delay between requests for safety. 

TODO:

1. Add a simple GUI
2. Ensure proper behavior on an account with 0 posts
3. Add ability to export URLS of non-deletable posts 
4. Add ability to choose custom placeholder text for edited posts
5. ???





# Installation Instructions:
1. Clone Repo
2. Install Python https://www.python.org/downloads/
3. Install pip https://pip.pypa.io/en/stable/installing/
4. Run: pip install -r requirements.txt
5. Run: python deleteposts.py




