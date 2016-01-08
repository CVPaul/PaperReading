import os
import urllib
import logging
import json

from google.appengine.ext import ndb
from google.appengine.api import app_identity

import Authentication as Auth

import jinja2
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

APPID = app_identity.app_identity.get_application_id()
HOSTNAME = app_identity.app_identity.get_default_version_hostname()

DEFAULT_PAPER_LIST=dict()
DEFAULT_USER_LIST=dict()
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

class voteUser(ndb.Model):
    count=ndb.IntegerProperty()

def user_key(email):
    return ndb.Key('voteUser',email)

def is_eng(text):
    for ch in text:
        if ord(ch)>127:
            return False
    return True

class MainPage(Auth.BaseHandler):

    def get(self):
        u = self.user_info
        if not self.user_info:
            user=None
        else:
            model=self.user_model.get_by_id(u['user_id'])
            user=model.email_address

        if user:
            url='logout'
            url_linktext = 'Logout'
        else:
            url='login'
            url_linktext = 'Login/Signup'

        config=config_key().get() # get the latest
        if not DEFAULT_PAPER_LIST:
            # start load the Paper List
            if config:
                papers_query=Paper.query(Paper.date>config.date)
            else:
                papers_query = Paper.query().order(-Paper.date)
            papers = papers_query.fetch(DEFAULT_COUNT)

            for paper in papers:
                key=paper.key.id()
                DEFAULT_PAPER_LIST[key]=[int(paper.vote),paper.descri,\
                        paper.owner,list(paper.vote_emails)]
            # end of the paper list load 
            # start of user list load
            user_query = voteUser.query()
            user_list=user_query.fetch()
            for usr in user_list:
                uk=usr.key.id()
                DEFAULT_USER_LIST[uk]=usr.count
            #end of the user list load
            # endfor

        #endif
        template_values = {
            'user': user,
            'user_list': json.dumps(DEFAULT_USER_LIST),
            'config': config,
            'url': url,
            'url_linktext':url_linktext,
            'papers': json.dumps(DEFAULT_PAPER_LIST),
            'default_list': urllib.quote_plus(DEFAULT_LIST),
        }

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))

class Paperlist(Auth.BaseHandler):

    def post(self):

        data = json.loads(self.request.body)
        if not data : return
        bibtex=data['bibtex']
        bibkey=data['bibkey']
        bibdes=data['descri']
        usr=data['usr']

        if not is_eng(bibtex):
            bibtex="".join(bibtex.split())# json not allowed space in Chinese string
        if not is_eng(bibkey):
            bibkey="".join(bibkey.split())# json not allowed space in Chinese string
        if not is_eng(bibdes):
            bibdes="".join(bibdes.split())# json not allowed space in Chinese string
        # here we do not deal with user name which have non ascii character (on 2016-01-08)
        paper=Paper(bibtex=bibtex,descri=bibdes,owner=usr,vote_emails=[],vote=0,id=bibkey)
        paper.put()

        DEFAULT_PAPER_LIST[bibkey]=[0,bibdes,usr,[]]

class Operation(Auth.BaseHandler):

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
            for ems in DEFAULT_PAPER_LIST[key_text][3]:
                DEFAULT_USER_LIST[ems]=DEFAULT_USER_LIST[ems]-1;
                usr_ems=user_key(ems).get()
                if not usr_ems or usr_ems.count==0:
                    continue
                usr_ems.count=usr_ems.count-1
                usr_ems.put()

            DEFAULT_PAPER_LIST.pop(key_text)
            key.delete()
        elif opr=='vot':
            usr_ems=user_key(usr).get()
            if not usr_ems:
                usr_ems=voteUser(count=0,id=usr)
            usr_ems.count=usr_ems.count+1
            usr_ems.put()

            npaper=key.get()
            npaper.vote=npaper.vote+1
            npaper.vote_emails.append(usr)
            npaper.put();
            DEFAULT_PAPER_LIST[key_text][0]=DEFAULT_PAPER_LIST[key_text][0]+1
            DEFAULT_PAPER_LIST[key_text][3].append(usr)
        elif opr=='can':
            usr_ems=user_key(usr).get()
            if not usr_ems or usr_ems.count==0:
                return
            usr_ems.count=usr_ems.count-1
            usr_ems.put()

            npaper=key.get()
            if npaper.vote<=0:
                return
            npaper.vote=npaper.vote-1
            npaper.vote_emails.remove(usr)
            npaper.put()
            DEFAULT_PAPER_LIST[key_text][0]=DEFAULT_PAPER_LIST[key_text][0]-1
            DEFAULT_PAPER_LIST[key_text][3].remove(usr)
        else:
            return
class Config(Auth.BaseHandler):
    
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


class Download(Auth.BaseHandler):

    def get(self):
        self.response.headers['Content-Type'] = 'application/octet-stream'
        self.response.headers['Content-Disposition']='attachment; filename=%s'%('bibtex.bib')
        
        papers_query = Paper.query().order(-Paper.date)
        papers = papers_query.fetch()

        data=""
        for p in papers:
            data=data+p.bibtex+'\n'
        self.response.out.write(data)
        
user_config = {
  'webapp2_extras.auth': {
    'user_model': 'models.User',
    'user_attributes': ['name']
  },
  'webapp2_extras.sessions': {
    'secret_key': 'YOUR_SECRET_KEY'
  }
}
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/upload', Paperlist),
    ('/config', Config),
    ('/operation',Operation),
    ('/download',Download),
    ('/login',Auth.LoginHandler),
    ('/forgot',Auth.ForgotPasswordHandler),
    ('/signup',Auth.SignupHandler),
    webapp2.Route('/<type:v|p>/<user_id:\d+>-<signup_token:.+>',
      Auth.VerificationHandler, name='verification'),
    ('/logout',Auth.LogoutHandler),
    ('/setting',Auth.SetPasswordHandler)
], debug=True,config=user_config)
