#### 1. Clone this repository and open new directory in VS Code
```sh
git clone https://github.com/levensailor/oldprognewtricks.git
cd oldprognewtricks
code .
```

#### 2. Create and activate Python Virtual Environment 🐍
```bash
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
Download for Mac OS and unzip to /usr/local/bin
Add authtoken
Run, forwarding http to port 5000
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
#### 5. Create Cisco Webex Teams Bot
https://developer.webex.com
Start building apps
Create new app
For type, select **Bot**
Fill out required information, and click Submit
 👉 Copy **access-token** for later


##### Create Dialogflow Agent
https://console.dialogflow.com
Add new agent
Select **Integrations** and paste **access token** from prior step 4
Select **Fulfillment** and paste the **forwarding url** from step 3
##### 
