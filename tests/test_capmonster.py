import os
import asyncio
import random

from requests import Session
from capmonstercloudclient import CapMonsterClient, ClientOptions
from capmonstercloudclient.requests import RecaptchaV2EnterpriseProxylessRequest
from latest_user_agents import get_random_user_agent

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


async def solve_captcha_async():
    task = asyncio.create_task(cap_monster_client.solve_captcha(recaptcha2request))
    return await asyncio.gather(task, return_exceptions=True)


if __name__ == '__main__':
    capmonster_api_key = os.getenv('CAPMONSTER_API_KEY')
    session = Session()
    session.headers.update({'User-Agent': get_random_user_agent(),
                            'Accept-Language': 'q=0.8,en-US;q=0.6,en;q=0.4'})
    session.headers.update({'Host': 'store.steampowered.com'})
    session.get("https://store.steampowered.com/join/")
    response = session.get('https://store.steampowered.com/join/refreshcaptcha', timeout=30).json()
    gid, sitekey, s = response['gid'], response['sitekey'], response['s']

    client_options = ClientOptions(api_key=capmonster_api_key)
    cap_monster_client = CapMonsterClient(options=client_options)

    recaptcha2request = RecaptchaV2EnterpriseProxylessRequest(websiteUrl='https://store.steampowered.com/join',
                                                              websiteKey=sitekey, enterprisePayload=s)
    async_responses = asyncio.run(solve_captcha_async())
    token = async_responses[0]["gRecaptchaResponse"]
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