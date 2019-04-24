## I. Environment Setup

#### 1. Clone this repository and open new directory in VS Code
```sh
git clone https://github.com/levensailor/oldprognewtricks.git
cd oldprognewtricks
code .
```

#### 2. Create and activate Python Virtual Environment 🐍
```bash
pip3 install virtualenv
virtualenv newtricks
source newtricks/bin/activate
(newtricks) user in ~/oldprognewtricks$ python -V
Python 3.6.5
```

#### 3. Install Requirements and Start Application
```bash
pip install -R requirements.txt
python app.py

Starting app on port 5000
 * Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)
 * Restarting with stat
```

#### 4. Create ngrok tunnel
##### https://ngrok.com
- Download for Mac OS
- Unzip to local path, ie: /usr/local/bin
- Add authtoken
- Run ngrok to forward http to port 5000
```
$ unzip /path/to/ngrok.zip -d /usr/local/bin/
$ ./ngrok authtoken 37eroiNyyQKWiyvj1Sx4b_64GfspoBskoWtAew7d2Be
$ ./ngrok http 5000
```
```bash
ngrok by @inconshreveable                                       (Ctrl+C to quit)

Session Status                online
Account                       Jeff Levensailor (Plan: Basic)
Version                       2.3.25
Region                        United States (us)
Web Interface                 http://127.0.0.1:4040
Forwarding                    http://3167e24f.ngrok.io -> http://localhost:5000
Forwarding                    https://3167e24f.ngrok.io -> http://localhost:5000
```
👉 Copy **forwarding url** for later

#### 5. Create Cisco Webex Teams Bot
https://developer.webex.com
- Start building apps
- Create new app
- For type, select **Bot**
- Fill out required information, and click Submit

👉 Copy **access-token** for later


##### Create Dialogflow Agent
https://console.dialogflow.com
- Add new agent
- Select **Integrations** and paste **access token** from prior step 5
- Select **Fulfillment** and paste the **forwarding url** from step 4
#####

## II. Entities

Entities are variables that use machine learning to make informed decisions on what data is given to fulfill an intent
Dialogflow, Lex and others have built-in entities for common items such as phone numbers, cities and email addresses
Custom entities: mac-address, service and username are below.

>@mac-address

| name     | synonymns   |
|----------|-------------|
| 2834A282A26C | 2834A282A26C|
| F8A5C59E0F1C | F8A5C59E0F1C|


>@service

| name                         | synonymns                           |
|------------------------------|-------------------------------------|
| Cisco CallManager            | callmanager, call manager           |
| Cisco Tomcat                 | tomcat, tom cat                     |
| Cisco CTIManager             | cti, ctimanager, cti manager        |
| Cisco Tftp                   | cisco tftp, tftp                    |
| Cisco Audit Logs             | auditlogs, audit logs               |
| Cisco Tomcat Security Logs   | security logs, tomcat security      |
| Cisco Corefile Recovery Tool | coredump, core, corefile, core dump |

>@username

| name                         | synonymns                           |
|------------------------------|-------------------------------------|
| dschrute                     | dschrute, dschrute's, dschrute?     |
| mscott                       | mscott, mscott's, mscott?           |
| pbeesly                      | pbeesly, pbeesly's, pbeesly?        |
| jhalpert                     | jhalpert, jhalpert's, jhalpert?     |

## III. Intents

#### 1. Reset Pin

> resetpin
- reset dschrute's pin to 1234
- change the pin to 1234 for csmith
- reset pin for john doe
- reset pin for jdoe
- change pin for dschrute to 1234

| Required | Parameter | Entity              | Value      | Prompt                  |
|----------|-----------|---------------------|------------|-------------------------|
|          | firstname | @sys.given-name     | $firstname |                         |
|          | lastname  | @sys.last-name      | $lastname  |                         |
| yes      | pin       | @sys.number-integer | $pin       | what pin should i make? |
|          | username  | @username           | $username  |                         |

#### 2. Fetch Number

>fetchnumber
- Fetch me the next 3 numbers in area code 424
- Fetch me 3 new numbers for chicago
- What is the next 2 available numbers in area code 919?
- I need 5 dids for atlanta


| Required | Parameter | Entity            | Value     | Prompt                   |
|----------|-----------|-------------------|-----------|--------------------------|
| yes      | number    | @sys.number       | $number   | How many should I fetch? |
|          | city      | @sys.geo-city     | $city     |                          |
|          | areacode  | @sys.phone-number | $areacode |                          |

#### 3. Check Device Registration

>checkreg
- can you tell me if 2020 is registered?
- check if phone number 2020 is registered
- is jim halpert's phone registered?
- check registration for 3245af31009b
- is there a phone registered for mscott?
- check registration for mscott

| Required | Parameter | Entity            | Value      | Prompt |
|----------|-----------|-------------------|------------|--------|
|          | username  | @username         | $username  |        |
|          | number    | @sys.phone-number | $number    |        |
|          | mac       | @mac-address      | $mac       |        |
|          | firstname | @sys.given-name   | $firstname |        |
|          | lastname  | @sys.last-name    | $lastname  |        |

#### 4. Take a Screenshot

>screenshot
- take a screenshot of michael scott's phone
- take a screenshot of mscott's phone
- take a picture of mscott's phone
- take a screenshot of 3300

| Required | Parameter | Entity            | Value      | Prompt |
|----------|-----------|-------------------|------------|--------|
|          | username  | @username         | $username  |        |
|          | number    | @sys.phone-number | $number    |        |
|          | firstname | @sys.given-name   | $firstname |        |
|          | lastname  | @sys.last-name    | $lastname  |        |

#### 5. Grab Status of Phone

>phonestatus
- what's up with michael scott's phone?
- what the status of michael scott's phone?
- what is the status of mscott's's phone?
- what is up with 2025?
- what's the status of 2025?

| Required | Parameter | Entity            | Value      | Prompt |
|----------|-----------|-------------------|------------|--------|
|          | username  | @username         | $username  |        |
|          | number    | @sys.phone-number | $number    |        |
|          | firstname | @sys.given-name   | $firstname |        |
|          | lastname  | @sys.last-name    | $lastname  |        |

#### 6. Collect Logs

>logs
- i need service logs from range
- i need service logs for the last 15 minutes

| Required | Parameter   | Entity           | Value        | Prompt                             |
|----------|-------------|------------------|--------------|------------------------------------|
| yes      | service     | @service         | $service     | what service do you need logs for? |
|          | duration    | @sys.duration    | $duration    |                                    |
|          | time-period | @sys.time-period | $time-period |                                    |
