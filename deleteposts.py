import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import re
import time


# Gets Message ID and Topic ID from the post's HTML
def get_post_info(post):

	outer_span = post.find("span", class_="category_header"); #div containing the post's info

	link_and_id = outer_span.find_all("a"); # getting link to the thread from the top banner
	thread_link = link_and_id[0]["href"];

	match = re.search("topic=([0-9]+)", thread_link); # extracting Topic ID from thread link

	if match:
		topic_id = match.group(1);
	else:
		print ("Error matching <essage ID");
		return;
	

	msg_id = link_and_id[1]['id'][3:]; #Getting Message ID from second <a></a> tag

	return  topic_id, msg_id;


# The Session Verification is in the form: <random(?) string>=<session ID>
# It is passed at the end of URLs when deleting and editing messages, 
# and also as a key/value pair in the multipart/formdata for editing posts. 
# Example session verification: bd31dd306428=d41d8cd98f00b204e9800998ecf8427e
# Session ID can be found on its own in the User Profile page
def get_session_verification(post):

	buttons_div = post.find("div", class_="post_buttons");
	button_links =  buttons_div.find_all("a");
	deletion_link = button_links[2]["href"];

	match = re.search("start=[0-9]*;([A-Fa-f0-9]+=[A-Fa-f0-9]+)", deletion_link); # extracting Session Verification from thread link

	if match:
		session_verification = match.group(1);
		return session_verification;
	else:
		print ("Error matching session verification");
		return None;

def construct_deletion_link(topic_id, msg_id, session_verification):
	return KTT_URL + "/forum/index.php?action=deletemsg;topic=" + topic_id + ";msg=" + msg_id +";" + session_verification;

def construct_deletion_referer(topic_id,msg_id):
	return KTT_URL + "/forum/index.php?topic=" + topic_id + ".msg" + msg_id + ";topicseen";

def construct_edit_link(topic_id, msg_id, session_verification):
	return KTT_URL + "/forum/index.php?action=post2;start=0;msg=" + msg_id + ";" + session_verification;

def construct_edit_referer(topic_id, msg_id):
	return KTT_URL + "/forum/index.php?action=post;msg=" + msg_id + ";topic=" + topic_id + ".0";

# Edits posts that the user does not have permission to delete.
# To edit a post: Send a POST request to http://www.kanyetothe.com/forum/index.php?action=post2;start=0;msg=<msg_id>;<session_verification>
# Referer: http://www.kanyetothe.com/forum/index.php?<msg_id>;topic=<topic_id>
# Seems to need the session_verification submitted as part of the multipart/formdata
# Also needs the topic ID and post button included as part of the form
# Response code (without redirects enabled) should be: HTTP/1.1 302 Found

def edit_post(topic_id, msg_id, session_verification):

	edit_link = construct_edit_link(topic_id, msg_id, session_verification);
	edit_referer = construct_edit_referer(topic_id, msg_id);

	edit_headers = DEFAULT_HEADERS;
	edit_headers["Referer"] = edit_referer;
	edit_headers["Origin"] = KTT_URL;

	hidden_info = session_verification.split("=");
	result = session.post(
	edit_link,
	files = {
			"subject": (None, "REMOVED"), 
			"message": (None, "REMOVED"), 
			"topic": (None, topic_id), 
			hidden_info[0] : (None, hidden_info[1]),
			"post": (None, "submit")
			},
	headers = edit_headers,
	allow_redirects=False
	);

	if(result.status_code != 302): 
		print("Failed to edit post. Either editing is disabled, the post does not exist, or you are not the author of this post.")
		error_msg = get_fatal_error(result.text);
		if error_msg:
			print("KTT Edit Error Message: " + error_msg);
	else:
		print("Succesfully edited the non-removable post.");
		
	
# To delete a post: 
# Send a POST request to http://www.kanyetothe.com/forum/index.php?action=deletemsg;topic=<t_id>;msg=m<id>;<verification>
# Referer: http://www.kanyetothe.com/forum/index.php?topic=<t_id>.msg<m_id>;topicseen
# Response code (without redirects enabled) should be: HTTP/1.1 302 Found
def delete_post(topic_id, msg_id, session_verification):

	deletion_link = construct_deletion_link(topic_id,msg_id,session_verification);
	deletion_referer = construct_deletion_referer(topic_id,msg_id);


	deletion_headers = DEFAULT_HEADERS;
	deletion_headers["Referer"] = deletion_referer;

	result = session.post(
		deletion_link,
		headers = deletion_headers,
		allow_redirects=False
	);

	if(result.status_code != 302): 
		print("Failed to delete post.");
		error_msg = get_fatal_error(result.text);
		if error_msg:
			print("KTT Deletion Error Message: " + error_msg);
		print(" Attempting to edit...");

		time.sleep(STANDARD_DELAY);
		edit_post(topic_id, msg_id, session_verification);
		#add to seen array
	else:
		print("Post Deleted Successfully.");



# Scrapes user's Posts page and returns the session_verification and a list of posts
# in the format "<topic_id>:<message_id>". Each page has a maximum of 18 posts. Each page
# can be accessed by adding "start=<multiple_of_18>" to the end of the Posts page url. 
def collect_posts():

	start = 0; 

	num_collected = 0;
	end_reached = False;

	collected_posts = [];
	session_verification = "";

	page = 1;

	print("Collecting Posts: ")
	while(not(end_reached)):
		print("Collecting Page " + str(page) + "...");

		result = session.get(POSTS_URL + "start=" + str(start));

		soup = BeautifulSoup(result.text, "html.parser");
		posts = soup.find_all("div", class_="category topicindex"); # find all posts on this page


		if (len(posts) == 0):
			error_msg = get_fatal_error(result.txt);
			if error_msg:
				print("Error reaching posts page.");
				print("KTT Error Message: " + error_msg);
				end_reached = True;
			else:
				print("This account doesn't seem to have any posts.");
		else:
			if (start == 0): # grab session verification from first available post
				session_verification = get_session_verification(posts[0]);

			for post in posts: # append this page's posts to list
				topic_id, msg_id = get_post_info(post);
				collected_posts.append(topic_id + ":" + msg_id);
				num_collected +=1;

		if (num_collected < 18):
			start += num_collected;
			end_reached = True;
		else:
			start += num_collected;
			num_collected = 0;
			page += 1;

		delay = time.time() - t0;
		time.sleep(STANDARD_DELAY);  # Delay next iteration/request 

	print(str(page) + " page(s) of posts have been collected. Total posts collected: " + str(start));
	return session_verification , collected_posts;


# Attempts to delete all posts in a given list of posts
# Posts are strings in the form "<topic_id>:<message_id"
def delete_posts(posts_list, session_verification):
	for post in posts_list:
		ids = post.split(":");
		topic_id = ids[0];
		msg_id = ids[1];

		delete_post(topic_id, msg_id, session_verification);
		time.sleep(STANDARD_DELAY);


# Searches response HTML for an Error from the KTT Website (response.text)
def get_fatal_error(response_text):
	s = BeautifulSoup(response_text, "lxml");
	error_block = s.find("div", id="fatal_error");
	if not(error_block):
		return None;
	error_msg = error_block.find(class_="padding").text;
	return error_msg;



def get_login_error(response_text):
	s = BeautifulSoup(response_text, "lxml");
	login_block = s.find("div", id="login");
	if not(login_block):
		return None;
	error_msg = login_block.find(class_="error").text;
	return error_msg;


def login():

	login_payload  = {
	"user" : "--------",
	"passwrd" : "-------",
	};	


	login_headers = DEFAULT_HEADERS;
	login_headers["Referer"] = "http://www.kanyetothe.com/forum/index.php?action=login";
	login_headers["Origin"] = KTT_URL;

	result = session.post(
		LOGIN_URL,
		data = login_payload,
		headers = login_headers,
		allow_redirects=False
	);

	if(result.status_code != 302):
		print("Failed to Log in.");
		error_msg = get_login_error(result.text);
		if error_msg:
			print("KTT Error Message: " + error_msg);
		return False;
	else:
		print("Logged in successfully.")
		return True;

def logout(session_verification):
	result = session.get(KTT_URL);

	print("Logging out...");
	logout_headers = DEFAULT_HEADERS;
	logout_headers['Referer'] = KTT_URL + "/forum/index.php";
	session_id = session_verification.split("=")[1];

	logout_url = KTT_URL + "/forum/index.php?action=logout;" + "sesc=" + session_id;
	result = session.get(
		logout_url,
		headers = logout_headers,
		allow_redirects = False
	);

	if(result.status_code != 302):
		print("Failed to Log out.");
		error_msg = get_login_error(result.text);
		if error_msg:
			print("KTT Error Message: " + error_msg);
		return False;
	else:
		print("Logged out successfully.")
		return True;

# ------------------------------------------Constants-----------------------------------------------

KTT_URL = "http://www.kanyetothe.com"
LOGIN_URL = "http://www.kanyetothe.com/forum/index.php?action=login2"
POSTS_URL = "http://www.kanyetothe.com/forum/index.php?action=profile;area=showposts;"

DEFAULT_HEADERS = {
	"Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
	"Accept-Encoding" :"gzip, deflate",
	"Accept-Language": "en-US,en;q=0.9,ja;q=0.8",
	"Upgrade-Insecure-Requests" : "1",
	"User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36",
}

STANDARD_DELAY = 5; # Delay between HTTP requests 



# --------------------------------------Main----------------------------------------

session = requests.Session();
retry = Retry(connect=3, backoff_factor=0.5);
adapter = HTTPAdapter(max_retries=retry);
session.mount('http://', adapter);
session.mount('https://', adapter);
session.headers = DEFAULT_HEADERS;

session.get(KTT_URL);


# Add user credentials to login_payload in login() to run, GUI to be added later 

if (login()):
	session_verification, collected_posts = collect_posts();
	#print(collected_posts);
	delete_posts(collected_posts);
	logout(session_verification);






