import imaplib
from ssl import SSLSession
import time
import re
from requests import Session
from steampy.utils import convert_edomain_to_imap
from steampy.login import LoginExecutor
from controller import InvalidEmail, AntiCaptcha


anticaptcha = AntiCaptcha()
anticaptcha.set_verbose(1)
anticaptcha.set_key("96c6a2734d83360b1f968e6e926c54d5")
anticaptcha.set_user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; \
                           x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36")


def authorize_email(email, email_password):
    email_domain = re.search(r"@(.+$)", email).group(1)
    imap_host = convert_edomain_to_imap(email_domain,  LoginExecutor.IMAP_HOSTS)

    if imap_host is None:
        raise InvalidEmail("Не удается найти imap host для данного email домена: %s" % email_domain)
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


def main():
    session = Session()
    session.headers.update({'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                           'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36'),
                            'Accept-Language': 'q=0.8,en-US;q=0.6,en;q=0.4'})
    session.headers.update({'Host': 'store.steampowered.com'})
    session.get("https://store.steampowered.com/join/")
    response = session.get('https://store.steampowered.com/join/refreshcaptcha/?count=1', timeout=30).json()
    gid, sitekey, s = response['gid'], response['sitekey'], response['s']
    anticaptcha.set_website_key(sitekey)
    anticaptcha.set_website_url('https://store.steampowered.com/join/refreshcaptcha/?count=1')
    anticaptcha.set_enterprise_payload({'s': s})

    cookies :str = ""
    for key, value in session.cookies.iteritems():
        cookies += key + "=" + value + ";"
    anticaptcha.set_cookies(cookies)

    token = anticaptcha.solve_and_return_solution()
    email = "awdasdwadawd@yandex.ru:viga9982"  # твоя почта
    creationid = confirm_email(session, gid, token, email)
    data = {
        'accountname': "wadwawasag1",  # логин для стим аккаунта
        'password': "Asdfelsk",  # пароль для стим аккаунта
        'count': '32',
        'lt': '0',
        'creation_sessionid': creationid
    }
    resp = session.post('https://store.steampowered.com/join/createaccount/',
                        data=data, timeout=25)
    print(resp.text)


main()
