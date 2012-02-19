import cgi
import datetime
import urllib
import wsgiref.handlers
import csv

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import mail
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import os
from google.appengine.ext.webapp import template

class Guest(db.Model):
  """Models an individual Guest and company Data"""
  #author = db.UserProperty()
  emailid = db.StringProperty()
  name = db.StringProperty()
  twitter = db.StringProperty()
  company = db.StringProperty()
  contact_no = db.StringProperty()
  tech = db.StringProperty()
  about_company = db.StringProperty(multiline=True)
  registered_on = db.DateTimeProperty(auto_now_add=True)
  r_id = db.EmailProperty()
  website = db.StringProperty()
  website2 = db.StringProperty()
  avatar = db.BlobProperty()
  devday = db.StringProperty()
  
  
class invite(db.Model):
    invite_code=db.StringProperty()
    r_id = db.EmailProperty()
    expiresOn = db.DateTimeProperty()
    isValid = db.BooleanProperty()
    devday = db.StringProperty()
    

def data_key(db_name=None):
  """Constructs a datastore key for a Guestbook entity with guestbook_name."""
  return db.Key.from_path('KeyStore', db_name or 'defaultDB')

class Image(webapp.RequestHandler):
    def get(self):
      greeting = db.get(self.request.get("img_id"))
      if greeting.avatar:
          self.response.headers['Content-Type'] = "image/png"
          self.response.out.write(greeting.avatar)
      else:
          self.error(404)

class ProcessInvite(webapp.RequestHandler):
      def get(self):
          invite_key=self.request.get('invite')
          if users.get_current_user():
              whois = users.get_current_user()
          else:
              whois= "Guest"
              
          #if users.get_current_user():
          #    url = users.create_logout_url(self.request.uri)
          #    url_linktext = 'Logout'
          #else:
          #    url = users.create_login_url(self.request.uri)
          #    url_linktext = 'Login'

          
          abhi = datetime.datetime.now()
          query = invite.all()
          query = query.filter('invite_code =',invite_key)
          exists = query.fetch(1)
          template_values = {
               # 'url': url,
               # 'url_linktext': url_linktext,
                'invite': invite_key,
                #'user':whois,
            }
          #if exists and abhi<=exists[0].expiresOn and exists[0].isValid:
          if exists and exists[0].isValid:
              path = os.path.join(os.path.dirname(__file__), 'login.html')
          else:
              path = os.path.join(os.path.dirname(__file__), 'invalid.html')
          self.response.out.write(template.render(path, template_values))

class Register(webapp.RequestHandler):
            def post(self):
                invite_key=self.request.get('invite')
                abhi = datetime.datetime.now()
                query = invite.all()
                query = query.filter('invite_code =',invite_key)
                exists = query.fetch(1)
                #if exists and abhi<=exists[0].expiresOn and exists[0].isValid:
                if exists and exists[0].isValid:
                    path = os.path.join(os.path.dirname(__file__), 'thankyou.html')
                else:
                    template_values={
                        'whois':"Guest",
                    }
                    path = os.path.join(os.path.dirname(__file__), 'invalid.html')
                    self.response.out.write(template.render(path, template_values))
                    return
                
                newguest = Guest(parent = data_key('guests'))
                newguest.devday = exists[0].devday
                newguest.emailid=self.request.get('emailid')
                newguest.name=self.request.get('name')
                newguest.twitter=self.request.get('twitter')
                newguest.company=self.request.get('company')
                newguest.contact_no=self.request.get('contact_no')
                newguest.tech=self.request.get('tech')
                newguest.about_company=self.request.get('about')
                newguest.website=self.request.get('website')
                newguest.website2=self.request.get('website2')
                avatar = self.request.get("img")
                #avatar = images.resize(self.request.get("img"), 100, 100)
                newguest.avatar = db.Blob(avatar)
                
                
                template_values={
                    'whois':newguest.name,
                }
                newguest.put()
                exists[0].isValid = False
                exists[0].put()
                
                self.response.out.write(template.render(path, template_values))

class MainPage(webapp.RequestHandler):
    def get(self):
        template_values={
        'user': 'random',
        }
        path = os.path.join(os.path.dirname(__file__), 'invite.html')
        self.response.out.write(template.render(path, template_values))

class Guestbook(webapp.RequestHandler):
  def post(self):
    # We set the same parent key on the 'Greeting' to ensure each greeting is in
    # the same entity group. Queries across the single entity group will be
    # consistent. However, the write rate to a single entity group should
    # be limited to ~1/second.
    guestbook_name = self.request.get('guestbook_name')
    greeting = Greeting(parent=guestbook_key(guestbook_name))

    if users.get_current_user():
      greeting.author = users.get_current_user()

    greeting.content = self.request.get('content')
    greeting.put()
    self.redirect('/?' + urllib.urlencode({'guestbook_name': guestbook_name}))

class AdminConsole(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'admin.html')
        if not users.is_current_user_admin():
            path = os.path.join(os.path.dirname(__file__), 'yuno.html')
        
        template_values={
        'login': users.create_login_url(self.request.uri),
        }
        
        self.response.out.write(template.render(path, template_values))
        
class AdminConsoleNoMail(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'adminnomail.html')
        if not users.is_current_user_admin():
            path = os.path.join(os.path.dirname(__file__), 'yuno.html')
        
        template_values={
        'login': users.create_login_url(self.request.uri),
        }
        
        self.response.out.write(template.render(path, template_values))
        
class AddKey(webapp.RequestHandler):
    def post(self):
        if not users.is_current_user_admin():
            self.redirect('/admin')
            return
        self.response.out.write("Adding Keys")
        newinvite = invite(parent=data_key())
        invite_key = self.request.get('invite')
        invitee = self.request.get('naam')
        newinvite.invite_code = invite_key
        newinvite.r_id = self.request.get('sendTo')
        newinvite.devday = self.request.get('devday')
        abhi = datetime.datetime.now()
        diff = datetime.timedelta(days=int(self.request.get('days')),hours=5,minutes=30)
        print (abhi+diff).date()
        newinvite.expiresOn = (abhi + diff)
        newinvite.isValid = True;
        #doesInviteExist = invite.
        query = invite.all()
        query = query.filter('invite_code =',invite_key)
        exists = query.fetch(5)
        if exists:
            self.response.out.write("<h1> DOH!!! Key already exists! </h1> Go back and try again with a new key... ")
            return
        #enter if all tests OK
        
        message = mail.EmailMessage()
        message.sender = "delhi.gtug@devfestx.com"
        message.to = self.request.get('sendTo')
        message.cc = "delhi.gtug@devfestx.com"
        message.bcc = "ra.rishab@gmail.com"
        message.subject = "Invitation to DevFestX"
        expiryDate = (abhi+diff).strftime("%b %d %Y %I:%M %p")
        message.html = """
        <html>

        <meta http-equiv="Content-Type" content="text/html;charset=UTF-8">
        <head>

            <link type="text/css" href="http://www.devfestx.com/gtug/delhi/2012/invite/style.css"></link>
        </head>
            <body leftmargin="0" marginwidth="0" topmargin="0" marginheight="0" offset="0" style="-webkit-text-size-adjust: none;margin: 0;padding: 0;background-color: #363636;width: 100%% !important;">
        	     <div id="gdd"> </div>

                                <table border="0" cellpadding="40" cellspacing="0" width="100%%" id="templateHeader" style="background:url(http://www.devfestx.com/gtug/delhi/2012/img/gdd.png);">
                                	<tr>

                                    	<td align="center" valign="top" style="padding-bottom: 20px;border-collapse: collapse;">
                                        	<table border="0" cellpadding="0" cellspacing="0" width="560">
                                            	<tr>
                                                    <td class="headerContent" style="border-collapse: collapse;color: #363636;font-family: Helvetica;font-size: 20px;font-weight: bold;line-height: 100%%;text-align: left;vertical-align: top;">
                                                        <div style="text-align: left;"><a href="http://gtug.devfestx.com/" style="color: #26ABE2;font-weight: normal;text-decoration: underline;"><img src="http://www.devfestx.com/gtug/delhi/2012/invite/images/DevFestX.png" alt="DevFestX , New Delhi 2012" border="0" style="margin: 0;padding: 0;max-width: 560px;border: 0;height: auto;line-height: 100%%;outline: none;text-decoration: none;" width="240" height="120" id="headerImage campaign-icon"></a></div>
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>

                                    </tr>
                                </table>



                                <table border="0" cellpadding="20" cellspacing="0" width="100%%" id="templateBody" style="background:url(http://www.devfestx.com/gtug/delhi/2012/img/gdd.png);">
                                	<tr>
                                    	<td align="center" valign="top" style="border-collapse: collapse;">
                                        	<table border="0" cellpadding="0" cellspacing="0" width="560">
                                            	<tr mc:repeatable="repeat_1" mc:repeatindex="0" mc:hideable="hideable_repeat_1_1" mchideable="hideable_repeat_1_1">
                                                	<td align="center" colspan="2" style="padding-bottom: 40px;border-collapse: collapse;">
                                                    	<table border="0" cellpadding="20" cellspacing="0" width="560" class="couponBlock" style="background-color: #ffffff;border: 1px dotted #303030;">

                                                        	<tr>
                                                            	<td width="200" style="border-collapse: collapse;">
                                                                	<div style="text-align: left;"><img src="http://www.devfestx.com/gtug/delhi/2012/invite/images/you_re_i.jpg" alt="" border="0" style="margin: 0;padding: 0;max-width: 200px;border: 0;height: auto;line-height: 100%%;outline: none;text-decoration: none;" width="200px" height="117"></div>
                                                                </td>
                                                                <td align="left" valign="top" style="padding-left: 10px;border-collapse: collapse;">
                                                                	<table border="0" cellpadding="0" cellspacing="0">
                                                                    	<tr>
                                                                        	<td colspan="2" valign="top" class="couponContent" style="border-collapse: collapse;color: #505050;font-family: Helvetica;font-size: 12px;line-height: 150%%;text-align: left;">Dear %s,<br>

        <br>
        You have been invited to <b>%s</b> of GTUG DevFestX , New Delhi 2012 . Your Invitation Code is : 
        <h1 style="color: #26ABE2;display: block;font-family: Helvetica;font-size: 60px;font-weight: normal;letter-spacing: -4px;line-height: 100%%;margin-top: 0;margin-right: 0;margin-bottom: 10px;margin-left: 0;text-align: left;">
        	<span style="font-family:lucida sans unicode,lucida grande,sans-serif;"><strong><span style="font-size:48px;">%s</span></strong></span></h1>
        <br>
        </td>
                                                                        </tr>
                                                                        <tr>
                                                                        	<td colspan="2" valign="top" class="couponContent" style="padding-top: 10px;border-collapse: collapse;color: #505050;font-family: Helvetica;font-size: 12px;line-height: 150%%;text-align: left;">To accept this invitation, click the following link,</td>
                                                                        </tr>

                                                                        <tr>
                                                                            <td valign="top" style="padding-top: 20px;border-collapse: collapse;">
                                                                            	<div class="couponContent" style="color: #505050;font-family: Helvetica;font-size: 12px;line-height: 150%%;text-align: left;"><a href="http://devfestx.appspot.com/process?invite=%s">http://devfestx.appspot.com/process?invite=%s</a><br>
        <br>
        <br>
         or copy and paste the code at devfestx.appspot.com: 
        <div style="text-align: left">
        	<span style="font-size:14px;"><br><br><strong>Please note that your invite expires on<br>
        	&nbsp; &nbsp; &nbsp; &nbsp; &nbsp;<span style="color:#ff0000;"> %s</span></strong></span><strong><span _fck_bookmark="1" style="display: none">&nbsp;</span><span style="font-size:14px;"><span style="color:#ff0000;">.</span><br>

        	Please register before this date.</span><br>
        	<br>
        	For queries mail us at <a href="mailto:delhi.gtug@devfestx.com" style="color: #26ABE2;font-weight: normal;text-decoration: underline;">delhi.gtug@devfestx.com</a></strong></div>
        <br>
        </div>
                                                                            </td>
                                                                        </tr>
                                                                    </table>

                                                                </td>
                                                            </tr>
                                                        </table>
                                                        <img src="http://www.devfestx.com/gtug/delhi/2012/invite/images/scissors.png" align="left" height="16" width="25" style="display: block;border: 0;height: auto;line-height: 100%%;outline: none;text-decoration: none;">
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>

                                </table>



                                <table border="0" cellpadding="20" cellspacing="0" width="100%%" id="templateFooter" style="border-top: 0;">
                                	<tr>
                                    	<td align="center" valign="top" style="border-collapse: collapse;">
                                        	<table border="0" cellpadding="0" cellspacing="0" width="560">
                                            	<tr>
                                                    <td valign="top" class="footerContent" style="padding-right: 20px;border-collapse: collapse;color: #909090;font-family: Helvetica;font-size: 11px;line-height: 125%%;text-align: left;">Copyright &copy; 2012 GTUG DevFestX, All rights reserved.<br>
        <br>
        <br>
        Powered by Google App Engine + Python. Built by <a href="http://rishab.in" style="color:#FFF">Rishab Arora</a> (<a href="https://twitter.com/#!/spacetime29" style="color:#FFF">@spacetime29</a>)
        <br><br>Our email address is:<br>
        delhi.gtug@devfestx.com&nbsp;<br>
        Template by mailchimp.com</td>
                                                </tr>
                                            </table>               
                            </td>
                        </tr>
                    </table>
                </center>
            </body>

        </html>
        """ % (invitee,newinvite.devday,invite_key,invite_key,invite_key,expiryDate) 
                     
        message.body = """
        Hey %s !
        You've received an invite to Day %s of DevFestX Delhi!

        To accept this invitation, click the following link,
        or copy and paste the URL into your browser's address
        bar:

        devfestx.appspot.com/process?invite=%s
        
        or enter the code %s 
        at devfestx.appspot.com
        
        Please note that your invite expires on %s . 
        Please register before this date. Contact delhi@devfestx.com for more information.
        Powered by Google App Engine, Python. Built by Rishab Arora ( @spacetime29 )
        """ % (invitee,newinvite.devday,invite_key,invite_key,expiryDate)

        message.send()
        
     
        newinvite.put()
        self.response.out.write("Added Keys")
       # self.redirect('/admin')
       
class AddKeyNoMail(webapp.RequestHandler):
    def post(self):
        if not users.is_current_user_admin():
            self.redirect('/admin')
            return
        self.response.out.write("Adding Keys")
        newinvite = invite(parent=data_key())
        invite_key = self.request.get('invite')
        invitee = self.request.get('naam')
        newinvite.invite_code = invite_key
        newinvite.r_id = self.request.get('sendTo')
        newinvite.devday = self.request.get('devday')
        abhi = datetime.datetime.now()
        diff = datetime.timedelta(days=int(self.request.get('days')),hours=5,minutes=30)
        print (abhi+diff).date()
        newinvite.expiresOn = (abhi + diff)
        newinvite.isValid = True;
        #doesInviteExist = invite.
        query = invite.all()
        query = query.filter('invite_code =',invite_key)
        exists = query.fetch(5)
        if exists:
            self.response.out.write("<h1> DOH!!! Key already exists! </h1> Go back and try again with a new key... ")
            return
        #enter if all tests OK
        newinvite.put()
        self.response.out.write("Added Keys")
       # self.redirect('/admin')
        
class ListKeys(webapp.RequestHandler):
    def get(self):
        if not users.is_current_user_admin():
            self.redirect('/admin')
            return
        self.response.out.write("List Keys<br>")
        allkeyslist = invite.all().ancestor(data_key())
        tenkey= allkeyslist.fetch(500)
        for key in tenkey:
            self.response.out.write(key.invite_code + ': ')
            self.response.out.write(key.r_id)
            self.response.out.write(' : ')
            self.response.out.write(key.expiresOn)
            self.response.out.write(' : isValid: ')
            self.response.out.write(key.isValid)
            self.response.out.write(' : for devday: ')
            self.response.out.write(key.devday)
            self.response.out.write('<br \>')
            
class ListGuestsCSV(webapp.RequestHandler):
    def get(self):
        if not users.is_current_user_admin():
            self.redirect('/admin')
            return
        allguest = Guest.all().ancestor(data_key('guests'))
        tenguests= allguest.fetch(500)
        self.response.out.write("CSV")     
        for newguest in tenguests:                                    
            whichday="nothing"
            whichday=newguest.devday             
            self.response.out.write("%s,%s,%s,%s,%s,%s,%s <br>" % (newguest.emailid,newguest.name,newguest.company, newguest.contact_no,newguest.website,newguest.website2,whichday))

class ListGuests(webapp.RequestHandler):
    def get(self):
        if not users.is_current_user_admin():
            self.redirect('/admin')
            return
        self.response.out.write("List Guests<br>")
        self.response.out.write("<link rel=\"stylesheet\" href=\"./css/stylelist.css\" media=\"all\" />")
        allguest = Guest.all().ancestor(data_key('guests'))
        tenguests= allguest.fetch(500)
        self.response.out.write("Total: %s <br><br>"%len(tenguests))
        day1=0
        day2=0
        for newguest in tenguests:
            whichday="nothing"
            divclass="contact"
            whichday=newguest.devday
            if whichday == "Day 2":
                day2=day2+1
                divclass="contactday2"
            else:
                day1=day1+1
            self.response.out.write("<div class=\"%s\"><img src='img?img_id=%s' height=100 width=100></img>" % (divclass,newguest.key()))

           
            self.response.out.write("""<li><b>Email: </b>%s
            <li><b>Name: </b>%s
            <li><b>Twitter: </b>%s
            <li><b>Affiliation: </b>%s
            <li><b>Phone: </b>%s
            <li><b>Tech: </b>%s
            <li class="about"><b>About: </b>%s
            <li><b>Website: </b>%s
            <li><b>Web2: </b>%s
            <li><b>Day: </b>%s
            <br />
            </div>

            """ % (newguest.emailid,newguest.name,newguest.twitter,newguest.company, newguest.contact_no,newguest.tech,newguest.about_company,newguest.website,newguest.website2,whichday))
        
        self.response.out.write("<br><br>Total Day 1: %s | Total Day 2: %s <br>"%(day1,day2))

class RClosed(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'closed.html')
        template_values={
        'login': users.create_login_url(self.request.uri),
        }
        self.response.out.write(template.render(path, template_values))   
        
         
#application = webapp.WSGIApplication([
#  ('/', MainPage),
#  ('/sign', Register),
#  ('/admin', AdminConsole),
#  ('/adminnomail', AdminConsoleNoMail),
#  ('/process',ProcessInvite),
#  ('/addkey',AddKey),
#  ('/nomail',AddKeyNoMail),
#  ('/Register',Register),
#  ('/listkeys',ListKeys),
#  ('/listguests',ListGuests),
#  ('/listguestscsv',ListGuestsCSV),
#  ('/img', Image)
#], debug=False)

application = webapp.WSGIApplication([
  ('/', RClosed),
  ('/sign', RClosed),
  ('/admin', AdminConsole),
  ('/adminnomail', AdminConsoleNoMail),
  ('/process',RClosed),
  ('/addkey',AddKey),
  ('/nomail',AddKeyNoMail),
  ('/Register',RClosed),
  ('/listkeys',ListKeys),
  ('/listguests',ListGuests),
  ('/listguestscsv',ListGuestsCSV),
  ('/img', Image)
], debug=True)


def main():
  run_wsgi_app(application)


if __name__ == '__main__':
  main()