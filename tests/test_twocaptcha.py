import imaplib
import os
import re
import time
import random

import dotenv
from requests import Session
import twocaptcha

# add path to steampy
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from steampy.utils import convert_edomain_to_imap
from latest_user_agents import get_random_user_agent

dotenv.load_dotenv()
resolver = twocaptcha.TwoCaptcha(os.getenv("TWOCAPTCHA_API_KEY"))


class InvalidEmail(Exception): pass


def authorize_email(email, email_password):
    email_domain = re.search(r"@(.+$)", email).group(1)
    imap_host = convert_edomain_to_imap(email_domain,
                                        additional_hosts={"imap.firstmail.ltd": ["fuymailer.online"]})

    if imap_host is None:
        raise Exception("Не удается найти imap host для данного email домена: %s", email_domain)
    server = imaplib.IMAP4_SSL(imap_host)
    server.login(email, email_password)
    server.select()
    return server


def fetch_confirmation_link(email, email_password, creationid):
    server = authorize_email(email, email_password)
    attempts = 0
    while attempts < 5:
        time.sleep(10)
        attempts += 1
        typ, data = server.search(None, 'ALL')
        uid = data[0].split()[-1]
        result, data = server.uid("fetch", uid, '(UID BODY[TEXT])')
        mail = data[0][1].decode('utf-8')
        url_search = re.search(r".*(https://.*newaccountverification.*creationid=3D(\w+))", mail, re.DOTALL)
        if url_search is None:
            time.sleep(10)
            continue
        link = url_search.group(1)
        creationid_from_url = url_search.group(2)
        if creationid == creationid_from_url:
            print("")
            time.sleep(10)
            continue
        server.close()
        return link

    server.close()
    raise InvalidEmail("Не удается получить письмо от Steam")


def confirm_email(session, gid, token, email: str):
    email_name, _, email_password = email.partition(":")
    data = {
        'captcha_text': token,
        'captchagid': gid,
        'email': email_name,
        'elang': 0
    }

    resp = session.post('https://store.steampowered.com/join/ajaxverifyemail', data=data).json()
    if resp["success"] == 101:
        raise InvalidEmail("Не удалось подтвердить email")
    creationid = resp['sessionid']
    time.sleep(10)  # wait some time until email has been received
    link = fetch_confirmation_link(email_name, email_password, creationid)
    session.get(link)
    return creationid


if __name__ == '__main__':
    session = Session()
    session.headers.update({'User-Agent': get_random_user_agent(),
                            'Accept-Language': 'q=0.8,en-US;q=0.6,en;q=0.4'})
    session.headers.update({'Host': 'store.steampowered.com'})
    session.get("https://store.steampowered.com/join/")
    response = session.get('https://store.steampowered.com/join/refreshcaptcha/', timeout=30).json()
    gid, sitekey, s = response['gid'], response['sitekey'], response['s']
    # cookies: str = ""
    # for key, value in session.cookies.iteritems():
    #     cookies += key + "=" + value + ";"
    # tocaptcha.set_cookies(cookies)

    result = resolver.recaptcha(sitekey, 'https://store.steampowered.com/join/refreshcaptcha/',
                                invisible=0, enterprise=1, datas=s)
    token = result["code"]
    with open("../resources/emails.txt") as f:
        emails = f.readlines()
    email = emails[random.randint(0, len(emails) - 1)].rstrip()
    creationid = confirm_email(session, gid, token, email)
    # randomize accountname and password
    credential = ["qwertyuiopasdfghjklzxcvbnm1234567890"]
    data = {
        'accountname': random.shuffle(credential[:8]),
        'password': random.shuffle(credential[:8]),
        'count': '32',
        'lt': '0',
        'creation_sessionid': creationid
    }
    resp = session.post('https://store.steampowered.com/join/createaccount/',
                        data=data, timeout=25)
    print(resp.text)
