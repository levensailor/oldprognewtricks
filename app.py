import sys
import os
import csv
import random
import time
import json
import shutil
import requests
from ciscoaxl import axl
from ciscoris import ris
from logs import logcollection
import boto3
from botocore.exceptions import ClientError
from webexteamssdk import WebexTeamsAPI
from requests.auth import HTTPBasicAuth
from phonescrape import scrape
from pprint import pformat
from flask import Flask, jsonify, request, abort, Response, make_response

'''
Setup Flask webhook
'''
app = Flask(__name__)
full  = os.path.abspath(os.path.dirname('.'))

'''
TODO - Enter Webex Teams token:
'''
token = '<your teams token here>'
teams = WebexTeamsAPI(access_token=token)

'''
Cisco CUCM service endpoints: AXL, RIS, CTI, Log Collection
'''
cucm = 'yo-dhzgwgcrwj.dynamic-m.com'
wsdl = 'https://s3-us-west-2.amazonaws.com/devnet2019/schema/12.5/AXLAPI.wsdl'
version = '12.5'
nat = True

axluser, axlpassword = ('administrator', 'D3vn3t2019')
axl = axl(username=axluser,password=axlpassword,wsdl=wsdl,cucm=cucm,cucm_version=version)

risuser, rispassword = ('administrator', 'D3vn3t2019')
ris = ris(username=risuser,password=rispassword,cucm=cucm,cucm_version=version)

ctiuser, ctipassword = ('ctiuser', 'D3vn3t2019')

sftpserver, sftpuser, sftppassword = ('yo-dhzgwgcrwj.dynamic-m.com', 'sftpuser', 'devnet')
log = logcollection(username=axluser, password=axlpassword, cucm=cucm, sftpserver=sftpserver, sftpusername=sftpuser, sftppassword=sftppassword)

'''
Amazon Dynamo will be used as a simple stack for logs
'''
dynamodb = boto3.resource('dynamodb', region_name="us-west-2")
table = dynamodb.Table('cache')

def update_db(req):
    roomId = req['originalDetectIntentRequest']['payload']['data']['data']['roomId']
    try:
        response = table.update_item(
        Key={
            'devnet': 'create'
        },
        UpdateExpression="set roomId = :r, wbxtoken = :t",
        ExpressionAttributeValues={
            ':r': roomId,
            ':t': token
        },
        ReturnValues="UPDATED_NEW"
        )
        return response
    except ClientError as e:
        return e.response['Error']['Message']

'''
Responses to intents are randomized for a human element
'''
def format_msg(result):
    success_fetchnumber = ["Dogo got you 👌🏽", "Dogo found dis 🔍", "Here what dogo found 👅"]
    fail_fetchnumber = ["Dogo not found ❌", "Dogo cannot find any 📟", "No numbers Dogo found 📞"]
    success_resetpin = ["Dogo accomplish 👍"]
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

'''
UTILITY FUNCTION
Return associated devices for a given username
'''
def get_phones_by_user(username):
    error = None
    phones = []
    res = axl.get_user(user_id=username)
    if res['success']:
        user = res['response']
        if 'associatedDevices' in user:
            for device in user['associatedDevices']:
                phones.append(device[1][0])
        return phones, error
    else:
        error = {'No devices found!'}
        return error

'''
UTILITY FUNCTION
Return associated devices for a given first and last name
'''
def get_phones_by_firstlast(firstname, lastname):
    error = None
    phones = []
    res = axl.get_users()
    for user in res:
        if user['firstName'].lower() == firstname.lower() and user['lastName'].lower() == lastname.lower():
            res = axl.get_user(user_id=user['userid'])
            if res['success']:
                user = res['response']
                if 'associatedDevices' in user:
                    for device in user['associatedDevices']:
                        phones.append(device[1][0])
                return phones, error
            else:
                error = {'No devices found!'}
                return error

'''
UTILITY FUNCTION
Return phones for a given number. Try "equals" before falling back to "contains". 
'''
def get_phones_by_number(number):
    error = None
    phones = []
    phone = {}
    res = axl.list_route_plan_specific(pattern=number)
    if res['success']:
        for each in res['response']:
            if 'dnOrPattern' in each:
                if each['type'] == 'Device':
                    phone['mac'] = each['routeDetail']['value']
                    phone['number'] = each['dnOrPattern']
                    phones.append(phone)
                else:
                    error = f'''{number} is a {each['type']}, not a phone'''
    else:
        res = axl.list_route_plan(pattern=number)
        if res['success']:
            for each in res['response']:
                if 'dnOrPattern' in each:
                    if each['type'] == 'Device':
                        phone['mac'] = each['routeDetail']['value']
                        phone['number'] = each['dnOrPattern']
                        phones.append(phone)
                    else:
                        error = f'''{number} is a {each['type']}, not a phone'''
        else:
            error = f'''{number} not found'''
    return phones, error

'''
UTILITY FUNCTION
Returns user info for a givne username
'''
def get_user_by_username(username):
    error = None
    res = axl.get_user(user_id=username)
    if res['success']:
        user = {}
        user['associatedDevices'] = res['response']['associatedDevices'][0]
        user['firstName'] = res['response']['firstName']
        user['lastName'] = res['response']['lastName']
        user['primaryExtension'] = res['response']['primaryExtension']['pattern']
        user['telephoneNumber'] = res['response']['telephoneNumber']
        user['directoryUri'] = res['response']['directoryUri']
        return user, error
    else:
        error = {'Something happened!'}
        return error

'''
UTILITY FUNCTION
Returns all subscribers with CallManager service running
'''
def get_subs():
    nodes = axl.listProcessNodes()
    if nodes['success']:
        return nodes['response']

'''
UTILITY FUNCTION
CTI authenticated screenshot retrieval
'''
def download_screenshot(ip):
    url = "https://"+ip+"/CGI/Screenshot"
    r = requests.get(url, auth=HTTPBasicAuth(ctiuser, ctipassword), verify=False, stream=True)
    with open('img.png', 'wb') as out_file:
        shutil.copyfileobj(r.raw, out_file)
    del r

'''
USES AXL

STEP 1: Use the appropriate axl function to fulfill the intent
'''
def resetpin(req):
    space = req['originalDetectIntentRequest']['payload']['data']['data']['roomId']
    username = req['queryResult']['parameters']['username']
    pin = str(int(req['queryResult']['parameters']['pin']))
    this_update_user = axl.update_user_credentials(username, pin=pin)
    if this_update_user['success']:
        msg = format_msg('success_resetpin')
        teams.messages.create(roomId=space, markdown=msg)
    else:
        msg = format_msg('fail_resetpin')
        teams.messages.create(roomId=space, markdown=msg)

'''
USES AXL

STEP 2: Use the appropriate axl function to fulfill the intent
'''
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

'''
USES RIS

STEP 3: Use the appropriate ris function 
STEP 4: For certain input, some utility functions will be required
'''
def checkreg(req):
    space = req['originalDetectIntentRequest']['payload']['data']['data']['roomId']
    username = req['queryResult']['parameters']['username']
    number = req['queryResult']['parameters']['number']
    mac = req['queryResult']['parameters']['mac']
    firstname = req['queryResult']['parameters']['firstname']
    lastname = req['queryResult']['parameters']['lastname']
    subs = get_subs()
    phones = []

    if mac:
        phones.append(mac)
        reg = ris.checkRegistration(phones, subs)
        status = reg['Status']
        timestamp = time.strftime('%m/%d/%Y %H:%M:%S', time.gmtime(reg['TimeStamp']))
        ipaddr = reg['IPAddress']['item'][0]['IP']
        msg = format_msg('success_checkreg')
        msg = msg + f'''Phone with mac address {mac} is {status} and has been since {timestamp}<br>'''
        msg = msg + f'''👉 Click <a href="https://{ipaddr}">here</a> to manage this phone'''
        teams.messages.create(roomId=space, markdown=msg)

    elif username:
        for res in get_phones_by_user(username):
            phones.append(res)
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
    
    elif number:
        res, error = get_phones_by_number(number)
        if error:
            msg = format_msg('fail_checkreg') + error
            teams.messages.create(roomId=space, markdown=msg)
        else:
            for phone in res:
                phones.append(phone['mac'])
                reg = ris.checkRegistration(phones, subs)
                status = reg['Status']
                timestamp = time.strftime('%m/%d/%Y %H:%M:%S', time.gmtime(reg['TimeStamp']))
                ipaddr = reg['IPAddress']['item'][0]['IP']
                msg = format_msg('success_checkreg')
                msg = msg + f'''Phone with number {phone['number']} is {status} and has been since {timestamp}<br>'''
                msg = msg + f'''👉 Click <a href="https://{ipaddr}">here</a> to manage this phone'''
                teams.messages.create(roomId=space, markdown=msg)

    elif firstname and lastname:
        res, error = get_phones_by_firstlast(firstname, lastname)
        if error:
            msg = format_msg('fail_checkreg') + error
            teams.messages.create(roomId=space, markdown=msg)
        else:
            reg = ris.checkRegistration(res, subs)
            status = reg['Status']
            timestamp = time.strftime('%m/%d/%Y %H:%M:%S', time.gmtime(reg['TimeStamp']))
            ipaddr = reg['IPAddress']['item'][0]['IP']
            msg = format_msg('success_checkreg')
            msg = msg + f'''{firstname} {lastname}'s phone is {status} and has been since {timestamp}<br>'''
            msg = msg + f'''👉 Click <a href="https://{ipaddr}">here</a> to manage this phone'''
            teams.messages.create(roomId=space, markdown=msg)

'''
Uses RIS

STEP 5: Use the appropriate ris function 
STEP 6: Some utility functions will be required
'''
def screenshot(req):
    space = req['originalDetectIntentRequest']['payload']['data']['data']['roomId']
    number = req['queryResult']['parameters']['number']
    username = req['queryResult']['parameters']['username']
    firstname = req['queryResult']['parameters']['firstname']
    lastname = req['queryResult']['parameters']['lastname']
    files = []
    phones = []
    subs = get_subs()
    if number:
        res, error = get_phones_by_number(number)
        if error:
            msg = format_msg('fail_screenshot') + error
            teams.messages.create(roomId=space, markdown=msg)
        else:
            for phone in res:
                phones.append(phone['mac'])
                reg = ris.checkRegistration(phones, subs)
                ip = reg['IPAddress']['item'][0]['IP']
                download_screenshot(cucm if nat else ip)
                msg = format_msg('success_screenshot')
                files.append('/'+full+'/img.png')
                teams.messages.create(roomId=space, markdown=msg, files=files)
                os.remove('/'+full+'/img.png')

    elif username:
        phone, error = get_phones_by_user(username)
        if error:
            msg = format_msg('fail_screenshot') + error
            teams.messages.create(roomId=space, markdown=msg)
        else:
            reg = ris.checkRegistration(phone, subs)
            for item in reg['IPAddress']['item']:
                ip = item['IP']
                download_screenshot(cucm if nat else ip)
                files.append('/'+full+'/img.png')
                msg = format_msg('success_screenshot')
                teams.messages.create(roomId=space, markdown=msg, files=files)

    elif firstname and lastname:
        phones, error = get_phones_by_firstlast(firstname, lastname)
        if error:
            msg = format_msg('fail_screenshot') + error
            teams.messages.create(roomId=space, markdown=msg)
        else:
            reg = ris.checkRegistration(phones, subs)
            for item in reg['IPAddress']['item']:
                ip = item['IP']
                download_screenshot(cucm if nat else ip)
                files.append('/'+full+'/img.png')
                msg = format_msg('success_screenshot')
                teams.messages.create(roomId=space, markdown=msg, files=files)

'''
Uses RIS, Phonescrape

STEP 7: Use the appropriate ris function
STEP 8: Use the appropriate scraping function
STEP 9: Utility functions will be required
'''
def phonestatus(req):
    space = req['originalDetectIntentRequest']['payload']['data']['data']['roomId']
    number = req['queryResult']['parameters']['number']
    username = req['queryResult']['parameters']['username']
    firstname = req['queryResult']['parameters']['firstname']
    lastname = req['queryResult']['parameters']['lastname']
    phones = []
    subs = get_subs()

    if number:
        res, error = get_phones_by_number(number)
        if error:
            msg = format_msg('fail_phonestatus') + error
            teams.messages.create(roomId=space, markdown=msg)
        else:
            for phone in res:
                phones.append(phone['mac'])
                reg = ris.checkRegistration(phones, subs)
                for item in reg['IPAddress']['item']:
                    ip = item['IP']
                    phone = scrape.allDetails(cucm if nat else ip)
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
    
    elif username:
        res, error = get_phones_by_user(username)
        if error:
            msg = format_msg('fail_phonestatus') + error
            teams.messages.create(roomId=space, markdown=msg)
        else:
            reg = ris.checkRegistration(res, subs)
            for item in reg['IPAddress']['item']:
                ip = item['IP']
                phone = scrape.allDetails(cucm if nat else ip)
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

    elif firstname and lastname:
        phones, error = get_phones_by_firstlast(firstname, lastname)
        if error:
            msg = format_msg('fail_phonestatus') + error
            teams.messages.create(roomId=space, markdown=msg)
        else:
            reg = ris.checkRegistration(phones, subs)
            for item in reg['IPAddress']['item']:
                ip = item['IP']
                phone = scrape.allDetails(cucm if nat else ip)
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

'''
USES LogCollection

STEP 10: Use the appropriate log function
'''
def logs(req):
    service = req['queryResult']['parameters']['service']
    duration = str(int(req['queryResult']['parameters']['duration']['amount']))
    time_period = req['queryResult']['parameters']['time-period']
    update_db(req)
    if duration:
        log.selectLogFilesRel(service=service, duration=duration)
    elif time_period:
        log.selectLogFilesAbs(service=service, time_period=time_period)

def default(req):
    space = req['originalDetectIntentRequest']['payload']['data']['data']['roomId']
    teams.messages.create(roomId=space, markdown='>Sorry.. not sure what you mean. Should I?')

def print_request(req):
        print('\n👇')
        print('query: '+req['queryResult']['queryText'])
        print('from: '+req['originalDetectIntentRequest']['payload']['data']['data']['personEmail'])
        print('intent: '+req['queryResult']['intent']['displayName']+ ', with a confidence of '+str(req['queryResult']['intentDetectionConfidence']))
        print(pformat(req['queryResult']['parameters']))
        print('☝️\n')

def process_request_from_dialogflow(req):
    print_request(req)
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
