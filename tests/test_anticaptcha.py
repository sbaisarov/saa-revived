import imaplib
import os
import re
import random
import sys

import dotenv
from requests import Session
from latest_user_agents import get_random_user_agent
from anticaptchaofficial.recaptchav2enterpriseproxyless import *

from mailbox import Mailbox, EmailConfirmationError

dotenv.load_dotenv()


def confirm_email(email, session, gid, token):
    data = {
        'captcha_text': token,
        'captchagid': gid,
        'email': email,
        'elang': 0
    }

    resp = session.post('https://store.steampowered.com/join/ajaxverifyemail', data=data).json()
    if resp["success"] == 101:
        raise EmailConfirmationError("Не удалось подтвердить email: %s" % resp["message"])
    creationid = resp['sessionid']
    time.sleep(10)  # wait some time until email has been received
    link = self.fetch_confirmation_link(creationid)
    session.get(link)
    return creationid


if __name__ == '__main__':
    session = Session()
    session.headers.update({'User-Agent': get_random_user_agent(),
                            'Accept-Language': 'q=0.8,en-US;q=0.6,en;q=0.4'})
    session.headers.update({'Host': 'store.steampowered.com'})
    with open("../emails.txt", "r") as f:
        emails = [email.strip() for email in f.readlines()]

    email = emails.pop()
    mailbox = Mailbox(email)
    registration_page = session.get('https://store.steampowered.com/join/')

    solver = recaptchaV2EnterpriseProxyless()
    solver.set_verbose(1)
    solver.set_key(os.getenv("ANTICAPTCHA_API_KEY"))
    solver.set_website_url("https://store.steampowered.com/join/")
    solver.set_website_key(sitekey)
    solver.set_enterprise_payload({"s": s})

    solver.set_soft_id(0)

    g_response = solver.solve_and_return_solution()
    if g_response != 0:
        print("g-response: " + g_response)
    else:
        print("task finished with error " + solver.error_code)


    creationid = confirm_email(session, gid, g_response, mailbox)
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

