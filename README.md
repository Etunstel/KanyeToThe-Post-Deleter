# KanyeToThe-Post-Deleter


# About
A Python script for mass-deleting all (deletable) posts from your [KanyeToThe](http://www.kanyetothe.com/forum/) account. Non-deletable posts will have their titles and body overwritten. 

The script should be working currently, but it still needs some additional testing.

TODO:
1. Ensure proper behavior on an account with 0 posts
2. ??



# Installation/Usage Instructions:
1. Clone this repository 
2. Install Python https://www.python.org/downloads/
3. Install pip https://pip.pypa.io/en/stable/installing/
4. Run: ```pip install -r requirements.txt```
5. Run: ```python deleteposts.py```


# Usage Notes:

```STANDARD_DELAY```, ```REPLACEMENT_TITLE```, and ```REPLACEMENT_MESSAGE``` in the "Constants" section in **deleteposts.py** can be changed according to the user's preferences. Other constants should not be changed. 

There is a default delay of 5 seconds between deletion/edit attempts. Lowering this number will delete posts faster, but it may increase the risk of an IP ban due to a high amount of HTTP requests in a short time. If your account has a large number of posts, it may be best to keep this value unchanged, or increase it. 

For edited posts, the title will be replaced with the value in ```REPLACEMENT_TITLE```, and the message body will be replaced with the value in ```REPLACEMENT_MESSAGE```. The default text for both of these is "Removed". Remember to include quotation marks around your text. 

Any links to posts that were edited will be saved in a file named **edited_posts.txt**. Any links to posts that could not be deleted or edited will be saved in a file named **failed_to_edit.txt**. You can try requesting their removal in the [KTT Help and Problems" Section](http://www.kanyetothe.com/forum/index.php?board=10.0).






