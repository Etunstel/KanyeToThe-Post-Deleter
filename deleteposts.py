import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import re
import time
import getpass



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

TIMEOUT = 30 # Default HTTP Request timeout
STANDARD_DELAY = 5 # Delay between HTTP requests 
REPLACEMENT_TITLE =  "Removed"
REPLACEMENT_MESSAGE = "Removed"




# ---------------------------------------Functions-------------------------------------------------

# Gets Message ID and Topic ID from the post's HTML
def get_post_info(post):

	outer_span = post.find("span", class_="category_header") #div containing the post's info

	link_and_id = outer_span.find_all("a") # getting link to the thread from the top banner
	thread_link = link_and_id[0]["href"]

	match = re.search("topic=([0-9]+)", thread_link) # extracting Topic ID from thread link

	if match:
		topic_id = match.group(1)
	else:
		print ("Error matching Message ID")
		return;
	

	msg_id = link_and_id[1]['id'][3:] #Getting Message ID from second <a></a> tag

	return  topic_id, msg_id


# The Session Verification is in the form: <random(?) string>=<session ID>
# It is passed at the end of URLs when deleting and editing messages, 
# and also as a key/value pair in the multipart/formdata for editing posts. 
# Example session verification: bd31dd306428=d41d8cd98f00b204e9800998ecf8427e
# Session ID can be found on its own in the User Profile page
def get_session_verification(post):

	buttons_div = post.find("div", class_="post_buttons")
	button_links =  buttons_div.find_all("a")
	deletion_link = button_links[2]["href"]

	match = re.search("start=[0-9]*;([A-Fa-f0-9]+=[A-Fa-f0-9]+)", deletion_link) # extracting Session Verification from thread link

	if match:
		session_verification = match.group(1)
		return session_verification
	else:
		print ("Error matching session verification")
		return None;

def construct_deletion_link(topic_id, msg_id, session_verification):
	return KTT_URL + "/forum/index.php?action=deletemsg;topic=" + topic_id + ";msg=" + msg_id +";" + session_verification

def construct_deletion_referer(topic_id,msg_id):
	return KTT_URL + "/forum/index.php?topic=" + topic_id + ".msg" + msg_id + ";topicseen"

def construct_edit_link(topic_id, msg_id, session_verification):
	return KTT_URL + "/forum/index.php?action=post2;start=0;msg=" + msg_id + ";" + session_verification

def construct_edit_referer(topic_id, msg_id):
	return KTT_URL + "/forum/index.php?action=post;msg=" + msg_id + ";topic=" + topic_id + ".0"

def construct_post_link(topic_id, msg_id):
	return KTT_URL + "/forum/index.php?topic=" + topic_id + ".msg" + msg_id


# Edits posts that the user does not have permission to delete.
# To edit a post: Send a POST request to http://www.kanyetothe.com/forum/index.php?action=post2;start=0;msg=<msg_id>;<session_verification>
# Referer: http://www.kanyetothe.com/forum/index.php?<msg_id>;topic=<topic_id>
# Seems to need the session_verification submitted as part of the multipart/formdata
# Also needs the topic ID and post button included as part of the form
# Response code (without redirects enabled) should be: HTTP/1.1 302 Found

def edit_post(topic_id, msg_id, session_verification):

	global edited_posts
	global failed_to_edit

	edit_link = construct_edit_link(topic_id, msg_id, session_verification)
	edit_referer = construct_edit_referer(topic_id, msg_id)

	edit_headers = DEFAULT_HEADERS
	edit_headers["Referer"] = edit_referer
	edit_headers["Origin"] = KTT_URL

	hidden_info = session_verification.split("=")
	result = session.post(
	edit_link,
	files = {
			"subject": (None, REPLACEMENT_TITLE), 
			"message": (None, REPLACEMENT_MESSAGE), 
			"topic": (None, topic_id), 
			hidden_info[0] : (None, hidden_info[1]),
			"post": (None, "submit")
			},
	headers = edit_headers,
	allow_redirects=False,
	timeout= TIMEOUT
	)

	if(result.status_code != 302): 
		print("Failed to edit post: Topic ID:" + topic_id + " Message ID: " + msg_id)
		error_msg = get_fatal_error(result.text)
		if error_msg:
			print("KTT Edit Error Message: " + error_msg)
		failed_to_edit.append(construct_post_link(topic_id, msg_id))
	else:
		print("Succesfully edited the non-removable post.")
		edited_posts.append(construct_post_link(topic_id, msg_id))
		
	
# To delete a post: 
# Send a POST request to http://www.kanyetothe.com/forum/index.php?action=deletemsg;topic=<t_id>;msg=m<id>;<verification>
# Referer: http://www.kanyetothe.com/forum/index.php?topic=<t_id>.msg<m_id>;topicseen
# Response code (without redirects enabled) should be: HTTP/1.1 302 Found
def delete_post(topic_id, msg_id, session_verification):

	deletion_link = construct_deletion_link(topic_id,msg_id,session_verification)
	deletion_referer = construct_deletion_referer(topic_id,msg_id)


	deletion_headers = DEFAULT_HEADERS;
	deletion_headers["Referer"] = deletion_referer

	result = session.post(
		deletion_link,
		headers = deletion_headers,
		allow_redirects=False,
		timeout= TIMEOUT
	)

	if(result.status_code != 302): 
		print("Failed to delete post: Topic ID:" + topic_id + " Message ID: " + msg_id)
		error_msg = get_fatal_error(result.text)
		if error_msg:
			print("KTT Deletion Error Message: " + error_msg)
		print("Attempting to edit...")

		time.sleep(STANDARD_DELAY)
		edit_post(topic_id, msg_id, session_verification)
	else:
		print("Post Deleted Successfully.")



# Scrapes user's Posts page and returns the session_verification and a list of posts
# in the format "<topic_id>:<message_id>". Each page has a maximum of 18 posts. Each page
# can be accessed by adding "start=<multiple_of_18>" to the end of the Posts page url. 
def collect_posts():

	start = 0

	num_collected = 0
	end_reached = False

	collected_posts = []
	session_verification = ""

	page = 1

	print("Collecting Posts: ")
	while(not(end_reached)):
		print("Collecting Page " + str(page) + "...")

		result = session.get(POSTS_URL + "start=" + str(start), timeout= TIMEOUT)

		soup = BeautifulSoup(result.text, "html.parser")
		posts = soup.find_all("div", class_="category topicindex") # find all posts on this page


		if (len(posts) == 0):
			error_msg = get_fatal_error(result.text)
			if error_msg:
				print("Error reaching page" + str(page) + ".")
				print("KTT Error Message: " + error_msg)
			elif page == 1:
				print("This account doesn't seem to have any posts.")
			end_reached = True;

		else:
			if (start == 0): # grab session verification from first available post
				session_verification = get_session_verification(posts[0])

			for post in posts: # append this page's posts to list
				topic_id, msg_id = get_post_info(post)
				collected_posts.append(topic_id + ":" + msg_id)
				num_collected +=1;

		if (num_collected < 18):
			start += num_collected
			end_reached = True
		else:
			start += num_collected
			num_collected = 0
			page += 1

		time.sleep(STANDARD_DELAY)  # Delay next iteration/request 

	print(str(page) + " page(s) of posts have been collected. Total posts collected: " + str(start))
	return session_verification , collected_posts


# Attempts to delete all posts in a given list of posts
# Posts are strings in the form "<topic_id>:<message_id"
def delete_posts(posts_list, session_verification):

	total = len(posts_list)
	post_num = 1

	for post in posts_list:
		ids = post.split(":")
		topic_id = ids[0]
		msg_id = ids[1]

		print("Deleting post " + str(post_num) + " of " + str(total) + "...")
		delete_post(topic_id, msg_id, session_verification)
		time.sleep(STANDARD_DELAY)
		post_num += 1


# Searches response HTML for an Error from the KTT Website (response.text)
def get_fatal_error(response_text):
	s = BeautifulSoup(response_text, "lxml")
	error_block = s.find("div", id="fatal_error")
	if not(error_block):
		return None
	error_msg = error_block.find(class_="padding").text
	return error_msg



def get_login_error(response_text):
	s = BeautifulSoup(response_text, "lxml")
	login_block = s.find("div", id="login")
	if not(login_block):
		return None
	error_msg = login_block.find(class_="error").text
	return error_msg


def login(user, pwrd):

	login_payload  = {
	"user" : user,
	"passwrd" : pwrd,
	}


	login_headers = DEFAULT_HEADERS
	login_headers["Referer"] = "http://www.kanyetothe.com/forum/index.php?action=login"
	login_headers["Origin"] = KTT_URL

	result = session.post(
		LOGIN_URL,
		data = login_payload,
		headers = login_headers,
		allow_redirects=False,
		timeout= TIMEOUT
	)
	
	if(result.status_code != 302):
		print("Failed to Log in.");
		error_msg = get_login_error(result.text)
		if error_msg:
			print("KTT Error Message: " + error_msg)
		return False
	else:
		print("Logged in successfully.")
		return True

def logout(session_verification):
	result = session.get(KTT_URL, timeout= TIMEOUT)

	logout_headers = DEFAULT_HEADERS;
	logout_headers['Referer'] = KTT_URL + "/forum/index.php"
	session_id = session_verification.split("=")[1]

	logout_url = KTT_URL + "/forum/index.php?action=logout;" + "sesc=" + session_id
	result = session.get(
		logout_url,
		headers = logout_headers,
		allow_redirects = False,
		timeout= TIMEOUT
	)

	if(result.status_code != 302):
		print("Failed to Log out.")
		error_msg = get_login_error(result.text)
		if error_msg:
			print("KTT Error Message: " + error_msg)
		return False
	else:
		print("Logged out successfully.")
		return True


def create_list_file(title, lst):
	if(lst == []):
		return False
	else:
		f = open(title, "w")
		for link in lst:
			f.write(link + "\n")
		f.close();
		return True


# --------------------------------------Main Script----------------------------------------

session = requests.Session()
retry = Retry(connect=5, backoff_factor=0.5, status_forcelist=[ 500, 502, 503, 504 ])
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)
session.headers = DEFAULT_HEADERS

session.get(KTT_URL, timeout= TIMEOUT)


logged_in = False

global edited_posts
edited_posts = []

global failed_to_edit
failed_to_edit = []


while(not(logged_in)):
	user = input("Enter your KTT Username: ")
	pwrd = getpass.getpass("Enter your password: ") # Using getpass hides password input while being typed in
	logged_in = login(user, pwrd)


session_verification, collected_posts = collect_posts()

if(collected_posts == []):
	print("This account has no posts. Logging out...")
	logout(session_verification)
else:
	cont = input("Continue and delete posts? (yes/no): ").lower()
	while(cont not in ("yes", "no")):
		cont = input("Continue and delete posts? (yes/no): ").lower()

	if cont == "yes":
		delete_posts(collected_posts, session_verification);

		print("Finished deleting posts.")

		if(create_list_file("failed_to_edit.txt", failed_to_edit)):
			print("\"failed_to_edit.txt\" has been created.")
		else:
			print("No posts failed to be edited. \"failed_to_edit.txt\" was not created. ")

		if(create_list_file("edited_posts.txt", edited_posts)):
			print("\"edited_posts.txt\" has been created.")
		else:
			print("No posts were edited. \"edited_posts.txt\" was not created.")

		print("Finished, logging out...")
		logout(session_verification)

	elif cont == "no" :
		print("Finished, logging out...")
		logout(session_verification)
	








