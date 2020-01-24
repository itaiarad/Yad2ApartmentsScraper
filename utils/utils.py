import smtplib
import ssl
from email.mime.text import MIMEText
from random import choice

import certifi
import regex
import urllib3
import yaml
from bs4 import BeautifulSoup
from config.config import *


def random_headers():
    return {'User-Agent': choice(DESKTOP_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}


def get_all_json_strings(raw_string):
    mod_string = raw_string.replace(':', ': ')
    mod_string = mod_string.replace('"', '')
    mod_string = mod_string.replace('https: ', '')

    pattern = regex.compile(r'\{(?:[^{}]|(?R))*\}')
    return pattern.findall(mod_string)


def remove_timeformat(raw_string):
    prog = regex.compile(r'[0-9][0-9]: [0-9][0-9]: [0-9][0-9]')
    for pattern in prog.findall(raw_string):
        raw_string = raw_string.replace(pattern, '')
    return raw_string


def remove_unwanted_in_url(raw_string):
    prog = regex.compile(r'\.jpg\?.=')
    for pattern in prog.findall(raw_string):
        raw_string = raw_string.replace(pattern, '')

    prog = regex.compile(r'\.php\?')
    for pattern in prog.findall(raw_string):
        raw_string = raw_string.replace(pattern, '')

    return raw_string


def remove_unwanted_office_about(raw_string):
    prog = regex.compile('office_about:.*[\s\S]+,is_plat')
    for pattern in prog.findall(raw_string):
        raw_string = raw_string.replace(pattern, '')
    return raw_string


def remove_comma_from_price(raw_string):
    prog = regex.compile(r'price.+?(?=₪)')
    for pattern in prog.findall(raw_string):
        raw_string = raw_string.replace(pattern, pattern.replace(',', ''))
    return raw_string


def decode_json_string(json_string):
    json_string = remove_timeformat(json_string)
    json_string = remove_unwanted_in_url(json_string)
    json_string = remove_unwanted_office_about(json_string)
    json_string = remove_comma_from_price(json_string)
    return yaml.load(json_string)


def get_apartments_string(url):
    http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
    response = http.request('GET', url, headers=random_headers())
    soup = BeautifulSoup(response.data, features="lxml")
    st = soup.text.find("markerItems") + len("markerItems") + 1
    en = soup.text.find("filterParams") - 1  # ',' sep
    return soup.text[st:en]


def get_url(raw_url, neighborhood, req):
    return raw_url.format(neighborhood=neighborhood, room_min=req['rooms']['min'], room_max=req['rooms']['max'],
                          price_min=req['price']['min'], price_max=req['price']['max'], parking=req['parking'])


def extract_important_info(apt_json):
    apt = {}

    for field in IMPORTANT_INFO:
        try:
            apt[field] = apt_json['data'][field]

            if field == 'images':
                apt[field] = ['https:' + str(x['src']) for x in apt_json['data']['images'].values()]
        except:
            print("couldn't find {} in {}".format(field, apt_json['data'].keys()))


def send_email(apt_lst):
    port = 587  # For starttls
    smtp_server = "smtp.gmail.com"
    sender_email = ""
    receiver_email = ""
    context = ssl.create_default_context()

    apts = ['apartment {}'.format(ind+1) + '\n{}'.format(str(x)) for ind, x in enumerate(apt_lst)]
    apts = '\n'.join(apts)
    message = """Hi there,
     iv'e found the following apartments just for you!\n
     """ + apts + '\nsee you later'

    message_plain = MIMEText(message, "plain")

    print(message)
    with smtplib.SMTP(smtp_server, port) as server:
        server.ehlo()  # Can be omitted
        server.starttls(context=context)
        server.ehlo()  # Can be omitted
        server.login(sender_email, '')
        server.sendmail(sender_email, receiver_email, message_plain.as_string())


def extract_important_info(apt_lst):
    new_apt_lst = []
    for aprt in apt_lst:
        data = decode_json_string(aprt)['data']
        new_apt = {'price': data['price'], 'street': data['street'], 'sqm': data['square_meters'],
                   'rooms': data['line_1'], 'parking': data['Parking_text'], 'street_2': data['row_1']}
        new_apt_lst.append(new_apt)
    return new_apt_lst
