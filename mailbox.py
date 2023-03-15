import re
import time
import imaplib
from typing import List, Dict


class InvalidEmail(Exception): pass


class EmailConfirmationError(Exception): pass


class Mailbox:

    def __init__(self, email, imap_hosts: Dict[str, List] = None):
        self.email = email
        self.imap_hosts = imap_hosts

    def authorize_email(self):
        domain = re.search(r"@(.+$)", self.email).group(1)
        imap_host = self.search_imap_host(domain,
                                          imap_hosts={"imap.firstmail.ltd": ["fuymailer.online"]})

        if imap_host is None:
            raise InvalidEmail("Не удается найти imap host для данного email домена: %s", domain)
        server = imaplib.IMAP4_SSL(imap_host)
        server.login(self.email, self.password)
        server.select()
        return server

    def fetch_confirmation_link(self, creationid):
        server = self.authorize_email()
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

    @staticmethod
    def search_imap_host(domain, imap_hosts: Dict[str, List] = None):
        imap_host = None
        imap_hosts_to_domains = {
            "imap.yandex.ru": ["yandex.ru"],
            "imap.mail.ru": ["mail.ru", "bk.ru", "list.ru", "inbox.ru", "mail.ua"],
            "imap.rambler.ru": ["rambler.ru", "lenta.ru", "autorambler.ru", "myrambler.ru", "ro.ru", "rambler.ua"],
            "imap.gmail.com": ["gmail.com", ],
            "imap.mail.yahoo.com": ["yahoo.com", ],
            "imap-mail.outlook.com": ["outlook.com", "hotmail.com"],
            "imap.aol.com": ["aol.com", ]
        }

        if imap_hosts is not None:
            imap_hosts_to_domains.update(imap_hosts)

        for imap_host, domains in imap_hosts_to_domains.items():
            if domain in domains:
                return imap_host

        return imap_host
