#Django
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.core.context_processors import csrf
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
# Python
import oauth2 as oauth
import cgi
import urlparse
import urllib
#Prologger
from github2.client import Github
from achievements.models import ProloggerUser
from achievements_analytics import AchievementsAnalytics
from settings import MEDIA_URL


authorize_url = 'https://github.com/login/oauth/authorize?'
access_token_url = 'https://github.com/login/oauth/access_token?'
redirect_url = 'http://localhost/oauth/callback/'


#TODO move these to settings.py
consumer_key = 'c4e2f51b2faaed2d1762'
consumer_secret = 'ca01dbc8e37a89b6de54e48fec27d85e02289314'

consumer = oauth.Consumer(consumer_key, consumer_secret)
client = oauth.Client(consumer)

def view(request, template):
	c = {}
	media = {'MEDIA_URL' : MEDIA_URL }
	c.update(csrf(request))
	c.update(media)
	username = request.POST.get('username', '')
	api_token = request.POST.get('api_token', '')
	github = Github(username=username, api_token=api_token)
	gh = {'github': github}
	#creating a dictionary for context
	u = {'username': username}
	# adding d to c dictionary
	c.update(u)
	c.update(gh)
	return render_to_response(template,  c)
	
def analyze_achievements(request):
	user = request.user
	prologger_user = ProloggerUser.objects.get(user=user)
	github_user = prologger_user.github_user
	github_apitoken = prologger_user.github_apitoken 
	ach = AchievementsAnalytics(github_user, github_apitoken, prologger_user)
	achi = ach.get_achievements()
	html = "<html><body>The current user is  %s, prologger_user is : %s, the github user : %s, and the api_token %s.</body><p>%s</p></html>" % (user, prologger_user , github_user, github_apitoken, achi)
	return HttpResponse(html)
	

def github_login(request):
    pass
	
def callback(request):
    """POST https://github.com/login/oauth/access_token?
    client_id=...&
    redirect_uri=http://www.example.com/oauth_redirect&
    client_secret=...&
    code=..."""
    code = request.GET['code']
    url = "%sclient_id=%s&redirect_uri=%s&client_secret=%s&code=%s" % (access_token_url, consumer_key, redirect_url, consumer_secret, code)
    print url
    f =  urllib.urlopen(url)
    response = dict(cgi.parse_qsl(f.read()))
    print response
    token =  response['access_token']
    github = Github(access_token=token)
    #kludge to get current user
    name =  github.users.show("")
    print name.login
    print name.email
    
    try:
        user = User.objects.get(username=name.login)
        print user
    except User.DoesNotExist:
        user = User.objects.create_user(username=name.login, email=name.email)
        # Save our permanent token and secret for later.
        profile = ProloggerUser()
        profile.user = user
        profile.oauthtoken = token
        profile.save()
        
        # Authenticate the user and log them in using Django's pre-built 
        # functions for these things.
        user = authenticate(username=name.login,password= token)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect('/accounts/login/')
    
def logout(request):
    logout(request)
    return HttpResponseRedirect('/')

def login(request):
	resp, content = client.request(authorize_url, "GET")
	if resp['status'] != '200':
	    raise Exception("Invalid response %s." % resp['status'])
	request_token = dict(urlparse.parse_qsl(content))
	url = "%sclient_id=%s&redirect_uri=%s" % (authorize_url, consumer_key, redirect_url)
	return HttpResponseRedirect(url)
	
