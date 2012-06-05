# -*- coding: utf-8 -*-


import argparse
argument_parser = argparse.ArgumentParser(description = 'Retrieve next Sunday\'s bible passage.', prog = 'python {}'.format(__file__))
argument_parser.add_argument('gmail_user', metavar='gmail-user', help = 'email sender')
argument_parser.add_argument('gmail_pass', metavar='gmail-pass', help = 'email password')
argument_parser.add_argument('target_email', metavar='target-email', help = 'target email')


args = argument_parser.parse_args()


from datetime import date, timedelta

today = date.today()
target = today + timedelta(days = -(today.weekday() + 1), weeks = 1)

url = 'http://www.katolikus.hu/igenaptar/{0.year}{0.month:02}{0.day:02}.html'.format(target)

import urllib

print 'Getting HTML'

html = urllib.urlopen(url).read()
#print html

import re

from bs4 import BeautifulSoup as Soup, element
soup = Soup(html)

result = ''
title = ''

print 'Parsing HTML tree'
for obj in soup.findAll('p'):
    if obj.findAll('p'):
        continue

    if obj.findAll('b') and not obj.findAll('i'):
        subobj = obj.findAll('font')[0]
        for subchild in subobj.children:
            if isinstance(subchild, element.Tag):
                result += u'<h2> {} </h2>\n'.format(subchild.text)

            elif subchild.strip():
                title = subchild.strip()[:-1]
                result += u'<h1> {} </h1>\n'.format(title)

        # html is broken on source page
        sub = re.findall('<i><b>([^<]+)', html)
        result += u'<h3> {} </h3>\n'.format(sub[0].decode('utf8'))

    #elif obj.findAll('i'):
    #    result += u'<h3> {} </h3>\n'.format(obj.text)

    elif obj.findAll('a'):
        result += u'\n<h4 class="page"> {} </h4>\n'.format(obj.text)

    else:
        result += u'<p> {} </p>\n'.format(obj.text)


print 'Writing result'
output = '/tmp/reading-{0.year}-{0.month:02}-{0.day:02}.html'.format(target)
open(output, 'w').write(result.encode('utf8'))


epubconfig = {
    'meta': {
        'title': 'Olvasmány {0.year}.{0.month:02}.{0.day:02}'.format(target),
        'language': 'hu',
        'id': '01234567890',
        'author': {
            'first_name': 'Szentírás',
            'last_name': '',
        }
    },
    'chapters': [
        {
            'title': title,
            'src': output,
        }
    ],
}

import json

print 'Writing config'
open('/tmp/readingconf.json', 'w').write(json.dumps(epubconfig, indent = 4))


print 'Running conversion'

from subprocess import call

command = 'python /Users/martin/Projects/EPubCreator/generate.py /tmp/readingconf.json /tmp/olvasmany-{0.year}-{0.month:02}-{0.day:02}'.format(target)
if call(command.split()):
    import sys
    sys.exit()

print 'Creating email'




import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders
import os


msg = MIMEMultipart()

msg['From'] = args.gmail_user
msg['To'] = args.target_email
msg['Subject'] = 'Reading {0.year}-{0.month:02}-{0.day:02}'.format(target)

msg.attach(MIMEText('Reading for next Sunday.'))

attach = '/tmp/olvasmany-{0.year}-{0.month:02}-{0.day:02}.mobi'.format(target)

part = MIMEBase('application', 'octet-stream')
part.set_payload(open(attach, 'rb').read())
Encoders.encode_base64(part)
part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(attach))
msg.attach(part)

print 'Sending email'

mailServer = smtplib.SMTP('smtp.gmail.com', 587)
mailServer.ehlo()
mailServer.starttls()
mailServer.ehlo()
mailServer.login(args.gmail_user, args.gmail_pass)
mailServer.sendmail(args.gmail_user, args.target_email, msg.as_string())
mailServer.close()

print 'Done'


