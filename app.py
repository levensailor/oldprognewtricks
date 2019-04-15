import sys
import os
import csv
import random
import time
from ciscoaxl import axl
from ciscoris import ris
import shutil
from webexteamssdk import WebexTeamsAPI
import json
from requests.auth import HTTPBasicAuth
import requests
from phonescrape import scrape
from pprint import pformat
from flask import Flask, jsonify, request, abort, Response, make_response

'''
sftp://10.131.202.249
sftpuser:devnet
'''

'''
Setup Flask webhook
'''
app = Flask(__name__)
full  = os.path.abspath(os.path.dirname('.'))
'''
Setup Webex Teams
'''
teams = WebexTeamsAPI(access_token='Y2NjOGZmZDctYzk3Yi00OWM1LWEwNzYtZDA1NmJhODZjMDI3ZmQ4ODFiZDQtN2Vi_PF84_2b89525d-d39b-4b8b-8814-2b235d777a10')

'''
Setup Caxl AXL
'''
cucm = 'yo-dhzgwgcrwj.dynamic-m.com'
username = 'administrator'
password = 'D3vn3t2019'
ctiuser = 'ctiuser'
version = '12.5'
wsdl = 'https://s3-us-west-2.amazonaws.com/devnet2019/schema/12.5/AXLAPI.wsdl'
axl = axl(username=username,password=password,wsdl=wsdl,cucm=cucm,cucm_version=version)
ris = ris(username=username,password=password,cucm=cucm,cucm_version=version)

#ris.checkRegistration


def format_msg(result):
    success_fetchnumber = ["Dogo got you 👌🏽", "Dogo found dis 🔍", "Here what dogo found 👅"]
    fail_fetchnumber = ["Dogo not found ❌", "Dogo cannot find any 📟", "No numbers Dogo found 📞"]
    success_resetpin = ["Dogo has reset 🌈", "Dogo got this 👌🏽"]
    fail_resetpin = ["Dogo does not know this person 🚷", "Dogo says new phone who dis? 👅", "Dogo cannot reset pin for user if there is no user 👻"]
    success_checkreg = ["Dogo found dis 🔍", "Dogo got you 👌🏽", "Dogo dug this up 👍", "Look what Dogo found 👀"]
    fail_checkreg = ["Dogo cannot check phone when there no phone 🤔", "Dogo not finding this phone. is phone?", "Dogo says what phone dis? 👅"]
    success_phonestatus = ["Dogo found dis 🔍", "Dogo got you 👌🏽", "Dogo dug this up 👍", "Look what Dogo found 👀"]
    fail_phonestatus = ["Dogo cannot check phone when no phone exists ⁉️", "Dogo not find this phone ❌", "Dogo says what phone dis? 👅"]
    success_screenshot = ["Dogo took picture 📸", "Dogo put on snapchat 📸", "Look what Dogo found 👀"]
    fail_screenshot = ["Dogo cannot find ❌", "Dogo cannot take picture of phone when no phone ❌"]
    success_logs = ["Dogo found dis 🤲", "Dogo dug this up 🗞", "Look what Dogo found 👀"]
    fail_logs = ["Dogo cannot fetch, Dogo on break 🌭", "Dogo cannot find those ⁉️", "Dogo dug and there are no logs ⁉️"]

    if result == 'success_fetchnumber':
        return f'<blockquote class=success><h3>{random.choice(success_fetchnumber)}</h3>\n'
    elif result == 'fail_fetchnumber':
        return f'<blockquote class=danger><h3>{random.choice(fail_fetchnumber)}</h3>\n'
    elif result == 'success_resetpin':
        return f'<blockquote class=success><h3>{random.choice(success_resetpin)}</h3>\n'
    elif result == 'fail_resetpin':
        return f'<blockquote class=danger><h3>{random.choice(fail_resetpin)}</h3>\n'
    elif result == 'success_checkreg':
        return f'<blockquote class=success><h3>{random.choice(success_checkreg)}</h3>\n'
    elif result == 'fail_checkreg':
        return f'<blockquote class=danger><h3>{random.choice(fail_checkreg)}</h3>\n'
    elif result == 'success_phonestatus':
        return f'<blockquote class=success><h3>{random.choice(success_phonestatus)}</h3>\n'
    elif result == 'fail_phonestatus':
        return f'<blockquote class=danger><h3>{random.choice(fail_phonestatus)}</h3>\n'
    elif result == 'success_screenshot':
        return f'<blockquote class=success><h3>{random.choice(success_screenshot)}</h3>\n'
    elif result == 'fail_screenshot':
        return f'<blockquote class=danger><h3>{random.choice(fail_screenshot)}</h3>\n'
    elif result == 'success_logs':
        return f'<blockquote class=success><h3>{random.choice(success_logs)}</h3>\n'
    elif result == 'fail_logs':
        return f'<blockquote class=danger><strong>{random.choice(fail_logs)}</strong>\n'
    else:
        return

def get_phones_by_user(username):
    res = axl.get_user(user_id=username)
    error = None
    devices = res['response']['associatedDevices'][0]
    return devices, error

def get_user_by_username(username):
    res = axl.get_user(user_id=username)
    user = {}
    user['associatedDevices'] = res['response']['associatedDevices'][0]
    user['firstName'] = res['response']['firstName']
    user['lastName'] = res['response']['lastName']
    user['primaryExtension'] = res['response']['primaryExtension']['pattern']
    user['telephoneNumber'] = res['response']['telephoneNumber']
    user['directoryUri'] = res['response']['directoryUri']
    return user

def get_phone_by_number(number):
    res = axl.list_route_plan_specific(pattern=number)
    error = None
    phone = {}
    if res['success'] and 'dnOrPattern' in res['response'][0]:
        if res['response'][0]['type'] == 'Device':
            phone['mac'] = res['response'][0]['routeDetail']['value']
            phone['number'] = res['response'][0]['dnOrPattern']
        else:
            error = f'''{number} is a {res['response'][0]['type']}, not a phone'''
    else:
        res = axl.list_route_plan(pattern=number)
        if res['success'] and 'dnOrPattern' in res['response'][0]:
            if res['response'][0]['type'] == 'Device':
                phone['mac'] = res['response'][0]['routeDetail']['value']
                phone['number'] = res['response'][0]['dnOrPattern']
            else:
                error = f'''{number} is a {res['response'][0]['type']}, not a phone'''
        else:
            error = f'''{number} not found'''
    return phone, error

def get_subs():
    nodes = axl.listProcessNodes()
    if nodes['success']:
        return nodes['response']

def download_screenshot(ip):
    url = "https://"+ip+"/CGI/Screenshot"
    r = requests.get(url, auth=HTTPBasicAuth(ctiuser, password), verify=False, stream=True)
    with open('img.png', 'wb') as out_file:
        shutil.copyfileobj(r.raw, out_file)
    del r

def fetchnumber(req):
    space = req['originalDetectIntentRequest']['payload']['data']['data']['roomId']
    amount = req['queryResult']['parameters']['number']
    city = req['queryResult']['parameters']['city']
    areacode = req['queryResult']['parameters']['areacode']

    free = []
    with open('num.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                line_count += 1
            elif amount > len(free):
                did = row[2]
                if row[0].lower() == city.lower() or row[1] == areacode:
                    res = axl.list_route_plan(pattern=did)
                    if res['success']:
                        if res['response'] == 'Empty':
                            free.append(did)
                    else:
                        pass
    if len(free) > 0:
        msg = format_msg('success_fetchnumber')
        for num in free:
            msg = msg+'- '+num+'\n'
    else:
        msg = format_msg('fail_fetchnumber')
        msg = f'{msg} <strong> for {city} </strong>'

    teams.messages.create(roomId=space, markdown=msg)


def resetpin(req):
    space = req['originalDetectIntentRequest']['payload']['data']['data']['roomId']
    username = req['queryResult']['parameters']['username']
    pin = str(int(req['queryResult']['parameters']['pin']))
    this_update_user = axl.update_user(userid=username, pin=pin)
    if this_update_user['success']:
        msg = format_msg('success_resetpin')
        teams.messages.create(roomId=space, markdown='>'+this_update_user['response'])
    else:
        msg = format_msg('fail_resetpin')
        teams.messages.create(roomId=space, markdown='>'+this_update_user['response'])

def checkreg(req):
    space = req['originalDetectIntentRequest']['payload']['data']['data']['roomId']
    username = req['queryResult']['parameters']['username']
    number = req['queryResult']['parameters']['number']
    mac = req['queryResult']['parameters']['mac']
    subs = get_subs()
    phones = []

    if mac is not '':
        phones.append(mac)
        reg = ris.checkRegistration(phones, subs)
        status = reg['Status']
        timestamp = time.strftime('%m/%d/%Y %H:%M:%S', time.gmtime(reg['TimeStamp']))
        ipaddr = reg['IPAddress']['item'][0]['IP']
        msg = format_msg('success_checkreg')
        msg = msg + f'''Phone with mac address {mac} is {status} and has been since {timestamp}<br>'''
        msg = msg + f'''👉 Click <a href="https://{ipaddr}">here</a> to manage this phone'''
        teams.messages.create(roomId=space, markdown=msg)

    elif username is not '':
        for phone in get_phones_by_user(username):
            phones.append(phone)
        reg = ris.checkRegistration(phones, subs)
        status = reg['Status']
        timestamp = time.strftime('%m/%d/%Y %H:%M:%S', time.gmtime(reg['TimeStamp']))
        ipaddr = reg['IPAddress']['item'][0]['IP']
        user = get_user_by_username(username)
        firstName = user['firstName']
        lastName = user['lastName']
        msg = format_msg('success_checkreg')
        msg = msg + f'''{firstName} {lastName}'s phone is {status} and has been since {timestamp}<br>'''
        msg = msg + f'''👉 Click <a href="https://{ipaddr}">here</a> to manage this phone'''
        teams.messages.create(roomId=space, markdown=msg)
    
    elif number is not '':
        phone, error = get_phone_by_number(number)
        if error:
            msg = format_msg('fail_checkreg') + error
            teams.messages.create(roomId=space, markdown=msg)
        else:
            phones.append(phone['mac'])
            reg = ris.checkRegistration(phones, subs)
            status = reg['Status']
            timestamp = time.strftime('%m/%d/%Y %H:%M:%S', time.gmtime(reg['TimeStamp']))
            ipaddr = reg['IPAddress']['item'][0]['IP']
            msg = format_msg('success_checkreg')
            msg = msg + f'''Phone with number {phone['number']} is {status} and has been since {timestamp}<br>'''
            msg = msg + f'''👉 Click <a href="https://{ipaddr}">here</a> to manage this phone'''
            teams.messages.create(roomId=space, markdown=msg)


def screenshot(req):
    space = req['originalDetectIntentRequest']['payload']['data']['data']['roomId']
    number = req['queryResult']['parameters']['number']
    username = req['queryResult']['parameters']['username']
    files = []
    phones = []
    subs = get_subs()
    if number is not '':
        phone, error = get_phone_by_number(number)
        if error:
            msg = format_msg('fail_screenshot') + error
            teams.messages.create(roomId=space, markdown=msg)
        else:
            phones.append(phone['mac'])
            reg = ris.checkRegistration(phones, subs)
            ip = reg['IPAddress']['item'][0]['IP']
            download_screenshot(ip)
            files.append('/'+full+'/img.png')
            msg = format_msg('success_screenshot')
            teams.messages.create(roomId=space, markdown=msg, files=files)
            os.remove('/'+full+'/img.png')

    elif username is not '':
        phone, error = get_phones_by_user(username)
        if error:
            msg = format_msg('fail_screenshot') + error
            teams.messages.create(roomId=space, markdown=msg)
        else:
            reg = ris.checkRegistration(phone, subs)
            for ipv4 in reg['IPAddress']['item']:
                ip = ipv4['IP']
                download_screenshot(ip)
                files.append('/'+full+'/img.png')
                msg = format_msg('success_screenshot')
                teams.messages.create(roomId=space, markdown=msg, files=files)


def phonestatus(req):
    space = req['originalDetectIntentRequest']['payload']['data']['data']['roomId']
    number = req['queryResult']['parameters']['number']
    username = req['queryResult']['parameters']['username']
    phones = []
    subs = get_subs()
    if number is not '':
        phone, error = get_phone_by_number(number)
        if error:
            msg = format_msg('fail_phonestatus') + error
            teams.messages.create(roomId=space, markdown=msg)
        else:
            phones.append(phone['mac'])
            reg = ris.checkRegistration(phones, subs)
            ip = reg['IPAddress']['item'][0]['IP']
            phone = scrape.allDetails(ip)
            sn = phone['sn']
            dn = phone['dn']
            mac = phone['mac_address']
            model = phone['model']
            dhcp = phone['dhcp_server']
            tftp = phone['tftp1']
            cucm1 = phone['cucm1']
            gateway = phone['gateway']
            subnet = phone['subnetmask']
            firmware = phone['firmware']
            msg = format_msg('success_phonestatus')
            msg = msg + f''' - dn: {dn}\n- model: {model}\n- sn: {sn}\n- mac: {mac}\n- ip: {ip}\n- mask: {subnet}\n- gw: {gateway}\n- tftp: {tftp}\n- cucm1: {cucm1}\n- firmware: {firmware}'''
            teams.messages.create(roomId=space, markdown=msg)
    elif username is not '':
        phone, error = get_phones_by_user(username)
        if error:
            msg = format_msg('fail_phonestatus') + error
            teams.messages.create(roomId=space, markdown=msg)
        else:
            reg = ris.checkRegistration(phone, subs)
            for ipv4 in reg['IPAddress']['item']:
                ip = ipv4['IP']
                phone = scrape.allDetails(ip)
                sn = phone['sn']
                dn = phone['dn']
                mac = phone['mac_address']
                model = phone['model']
                dhcp = phone['dhcp_server']
                tftp = phone['tftp1']
                cucm1 = phone['cucm1']
                gateway = phone['gateway']
                subnet = phone['subnetmask']
                firmware = phone['firmware']
                msg = format_msg('success_phonestatus')
                msg = msg + f''' - dn: {dn}\n- model: {model}\n- sn: {sn}\n- mac: {mac}\n- ip: {ip}\n- mask: {subnet}\n- gw: {gateway}\n- tftp: {tftp}\n- cucm1: {cucm1}\n- firmware: {firmware}'''
                teams.messages.create(roomId=space, markdown=msg)

def logs(req):
    space = req['originalDetectIntentRequest']['payload']['data']['data']['roomId']
    service = req['queryResult']['parameters']['service']
    last_duration = req['queryResult']['parameters']['last_duration']
    teams.messages.create(roomId=space, markdown='```json\nreq\n```')
    print(req)

def default(req):
    space = req['originalDetectIntentRequest']['payload']['data']['data']['roomId']
    teams.messages.create(roomId=space, markdown='>Sorry.. not sure what you mean. Should I?')

def process_request_from_dialogflow(req):
    print(req)
    if 'source' in req['originalDetectIntentRequest']['payload']:
        intent = req['queryResult']['intent']['displayName']
        if intent == 'fetchnumber':
            fetchnumber(req)
        elif intent == 'resetpin':
            resetpin(req)
        elif intent == 'checkreg':
            checkreg(req)
        elif intent == 'screenshot':
            screenshot(req)
        elif intent == 'phonestatus':
            phonestatus(req)
        elif intent == 'logs':
            logs(req)
        else:
            default(req)
    else:
        print('dialogflow console test')

@app.route('/webhook',methods=['POST'])
def webhook():
    req = request.json
    process_request_from_dialogflow(req)
    return jsonify({'okay': 'okay'})


if __name__ == '__main__':
    port = 5000
    print("Starting app on port %d" % port)
    app.run(debug=True, port=port, host='0.0.0.0')