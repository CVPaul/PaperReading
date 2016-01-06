import os
import urllib
import logging
import json

from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.api import app_identity

import jinja2
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

APPID = app_identity.app_identity.get_application_id()
HOSTNAME = app_identity.app_identity.get_default_version_hostname()

DEFAULT_PAPER_LIST=dict()
DEFAULT_COUNT=10
DEFAULT_LIST='default_list'

config=None
GLOBAL_CONFIG="global_config"

class Paper(ndb.Model):
    """A main model for representing an individual Paperlist entry."""
    bibtex = ndb.StringProperty(indexed=False)
    descri = ndb.StringProperty(indexed=False)
    owner=ndb.StringProperty(indexed=False)
    vote_emails=ndb.StringProperty(repeated=True)
    vote=ndb.IntegerProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)

class config_param(ndb.Model):
    max_vote=ndb.IntegerProperty()
    Speaker1=ndb.StringProperty()
    Speaker2=ndb.StringProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)

def config_key():
    return ndb.Key('config_param',GLOBAL_CONFIG)

class MainPage(webapp2.RequestHandler):

    def get(self):
        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        if not DEFAULT_PAPER_LIST:
            
            papers_query = Paper.query().order(-Paper.date)
            papers = papers_query.fetch(DEFAULT_COUNT)

            for paper in papers:
                key=paper.key.id()
                DEFAULT_PAPER_LIST[key]=[int(paper.vote),paper.descri,paper.owner,list(paper.vote_emails)]

            # endfor

        #endif
        config=config_key().get() # get the latest
        template_values = {
            'user': user,
            'config': config,
            'url': url,
            'url_linktext':url_linktext,
            'papers': DEFAULT_PAPER_LIST,
            'default_list': urllib.quote_plus(DEFAULT_LIST),
        }

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))

class Paperlist(webapp2.RequestHandler):

    def post(self):

        data = json.loads(self.request.body)
        if not data : return
        bibtex=data['bibtex']
        bibkey=data['bibkey']
        bibdes=data['descri']
        usr=data['usr']
        paper=Paper(bibtex=bibtex,descri=bibdes,vote=0,id=bibkey)
        paper.put()

        DEFAULT_PAPER_LIST[bibkey]=[0,bibdes,usr,[]]

class Operation(webapp2.RequestHandler):

    """this function is defined to process the deleting,voting and un-voting of a paper"""
    def post(self):
        data=json.loads(self.request.body)
        if not data:
            return
        key_text=data['bibkey']
        opr=data['operator']
        usr=data['usr']

        key=ndb.Key('Paper',key_text)
        if opr=='del':
            DEFAULT_PAPER_LIST.pop(key_text)
            key.delete()
        elif opr=='vot':
            npaper=key.get()
            npaper.vote=npaper.vote+1
            npaper.put();
            DEFAULT_PAPER_LIST[key_text][0]=DEFAULT_PAPER_LIST[key_text][0]+1;
        elif opr=='can':
            npaper=key.get()
            if npaper.vote<=0:
                return
            npaper.vote=npaper.vote-1
            npaper.put()
            DEFAULT_PAPER_LIST[key_text][0]=DEFAULT_PAPER_LIST[key_text][0]-1;
        else:
            return
class Config(webapp2.RequestHandler):
    
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('config.html')
        self.response.write(template.render())

    def post(self):
        max_vote=int(self.request.get('max_vote'))
        speaker1=self.request.get('speaker1')
        speaker2=self.request.get('speaker2')
        
        #update the config file
        key=config_key()
        cfg=key.get()
        if not cfg:
            cfg=config_param(max_vote=max_vote,Speaker1=speaker1,Speaker2=speaker2,id=GLOBAL_CONFIG)
        else:
            cfg.max_vote=max_vote
            cfg.Speaker1=speaker1
            cfg.Speaker2=speaker2

        cfg.put()

        query_params = {'default_list': DEFAULT_LIST}
        self.redirect('/?' + urllib.urlencode(query_params))
        
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/upload', Paperlist),
    ('/config', Config),
    ('/operation',Operation)
], debug=True)
