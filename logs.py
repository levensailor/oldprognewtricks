"""
Class to interface with cisco ucm ris api.
Author: Jeff Levensailor
Version: 1.0.0
Dependencies:
 - suds-jurko: https://bitbucket.org/jurko/suds

Links:
 - https://developer.cisco.com/docs/sxml/#risport70-api-reference
"""
import os
import sys
import requests
import urllib.request
from base64 import b64decode, b64encode
from xml.sax.saxutils import unescape
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import subprocess
cwd  = os.path.abspath(os.path.dirname('.'))
sys.path.append(cwd)

class logcollection(object):

    def __init__(self, username, password, cucm, sftpserver, sftpusername, sftppassword):

        self.auth = self.encode(username, password)
        self.cucmurl = "https://"+cucm+":8443/logcollectionservice/services/LogCollectionPort"
        #self.legacy_url = "https://"+cucm+":8443/logcollectionservice/services/LogCollectionPort"
        self.sftpserver = sftpserver
        self.sftpusername = sftpusername
        self.sftppassword = sftppassword
    """

    """
    tags = []
    links = []

    def between_two_tags(self, s, sub1, sub2):
        tags=self.tags
        if sub1 in s and sub2 in s:
            tags.append(s[(s.index(sub1)+len(sub1)):s.index(sub2)])
            self.between_two_tags(s[(s.index(sub2)+len(sub2)):len(s)],sub1,sub2)
        return tags

    def get_url_paths(self, url, ext, tag='', params={}):
        links=self.links
        if url.endswith(tag):
            links.append(url)
        else:
            response = requests.get(url, params=params)
            if response.ok:
                response_text = response.text
            else:
                return response.raise_for_status()
            soup = BeautifulSoup(response_text, 'html.parser')
            if [node.get('href') for node in soup.find_all('a') if node.get('href')]:
                try:
                    for path in [url + node.get('href') for node in soup.find_all('a')]:
                        self.get_url_paths(url=path, ext=ext, tag=tag)
                except TypeError:
                    pass
            else:
                pass
        return links

    def encode(self, username, password):
        """Returns an HTTP basic authentication encrypted string given a valid
        username and password.
        """
        if ':' in username:
            raise EncodeError

        username_password = '%s:%s' % (username, password)
        return 'Basic ' + b64encode(username_password.encode()).decode()



    def listNodeServiceLogs(self):
        headers = {
        'Content-Type': "text/xml",
        'SOAPAction': '"listNodeServiceLogs"',
        "Authorization": self.auth
        }
        payload = "<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:soap=\"http://schemas.cisco.com/ast/soap\">\n   <soapenv:Header/>\n   <soapenv:Body>\n      <soap:listNodeServiceLogs>\n         <soap:ListRequest>?</soap:ListRequest>\n      </soap:listNodeServiceLogs>\n   </soapenv:Body>\n</soapenv:Envelope>"
        res = requests.request("POST", self.url, data=payload, headers=headers, verify=False)
        xml_response = unescape(res.text)
        tags = self.between_two_tags(s=xml_response,sub1='<ns1:item>',sub2='</ns1:item>')
        for tag in tags:
            if tag is not None:
                print(tag)

    def getTimeZone(self):
        headers = {
        'Content-Type': "text/xml",
        'SOAPAction': '"getTimeZone"',
        "Authorization": self.auth
        }
        payload = "<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:soap=\"http://schemas.cisco.com/ast/soap\">\n   <soapenv:Header/>\n   <soapenv:Body>\n      <soap:LocalHost>?</soap:LocalHost>\n   </soapenv:Body>\n</soapenv:Envelope>"
        res = requests.request("POST", self.cucmurl, data=payload, headers=headers, verify=False)
        xml_response = unescape(res.text)
        tags = self.between_two_tags(s=xml_response,sub1='<TimeZone>',sub2='</TimeZone>')
        for tag in tags:
            print(tag)
    
    def getOneFile(self):
        headers = {
        'Content-Type': "text/xml",
        'SOAPAction': '"getTimeZone"',
        "Authorization": self.auth
        }
        payload = "<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:soap=\"http://schemas.cisco.com/ast/soap\">\n   <soapenv:Header/>\n   <soapenv:Body>\n      <soap:LocalHost>?</soap:LocalHost>\n   </soapenv:Body>\n</soapenv:Envelope>"
        res = requests.request("POST", self.url, data=payload, headers=headers, verify=False)
        xml_response = unescape(res.text)
        tags = self.between_two_tags(s=xml_response,sub1='<TimeZone>',sub2='</TimeZone>')
        for tag in tags:
            print(tag)
    
    def selectLogFilesRel(self, service, duration):
        print(service)
        print(duration)
        units = 'Minutes'
        sftpserver = self.sftpserver
        sftpuser = self.sftpusername
        sftppassword = self.sftppassword
        url = 'http://'+sftpserver+':8000/'
        ext = 'gz'

        headers = {
        'Content-Type': "text/xml",
        'SOAPAction': '"selectLogFiles"',
        "Authorization": self.auth
        }
        paynode = "<soapenv:Envelope xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\" xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:soap=\"http://schemas.cisco.com/ast/soap/\">\n   <soapenv:Header/>\n   <soapenv:Body>\n      <soap:SelectLogFiles soapenv:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\">\n         <FileSelectionCriteria xsi:type=\"log:SchemaFileSelectionCriteria\" xmlns:log=\"http://cisco.com/ccm/serviceability/soap/LogCollection/\">\n            <ServiceLogs xsi:type=\"log:ArrayOfString\">\n               <!--Zero or more repetitions:-->\n               <item xsi:type=\"xsd:string\">"+service+"</item>\n            </ServiceLogs>\n            <SystemLogs xsi:type=\"log:ArrayOfString\">\n               <!--Zero or more repetitions:-->\n               <item xsi:type=\"xsd:string\"/>\n            </SystemLogs>\n            <SearchStr/>\n            <Frequency xsi:type=\"log:Frequency\">OnDemand</Frequency>\n            <JobType xsi:type=\"log:JobType\">PushtoSFTPServer</JobType>\n            <TimeZone/>\n            <RelText xsi:type=\"log:RelText\">"+units+"</RelText>\n            <RelTime xsi:type=\"xsd:byte\">"+duration+"</RelTime>\n            <Port xsi:type=\"xsd:byte\">22</Port>\n            <IPAddress xsi:type=\"xsd:string\">"+sftpserver+"</IPAddress>\n            <UserName xsi:type=\"xsd:string\">"+sftpuser+"</UserName>\n            <Password xsi:type=\"xsd:string\">"+sftppassword+"</Password>\n            <ZipInfo xsi:type=\"xsd:boolean\">False</ZipInfo>\n            <RemoteFolder xsi:type=\"xsd:string\">tmp</RemoteFolder>\n         </FileSelectionCriteria>\n      </soap:SelectLogFiles>\n   </soapenv:Body>\n</soapenv:Envelope>"

        payload = f'''\
            <soapenv:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:soap="http://schemas.cisco.com/ast/soap/">
            <soapenv:Header/>
            <soapenv:Body>
            <soap:SelectLogFiles soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
            <soap:FileSelectionCriteria xsi:type="log:SchemaFileSelectionCriteria" xmlns:log="http://cisco.com/ccm/serviceability/soap/LogCollection/">
            <soap:ServiceLogs xsi:type="log:ArrayOfString">
                <item xsi:type="xsd:string">{service}</item>
            </soap:ServiceLogs>
            <SystemLogs xsi:type="log:ArrayOfString">
                <item xsi:type="xsd:string"/>
            </SystemLogs>
            <SearchStr/>
            <Frequency xsi:type="log:Frequency">OnDemand</Frequency>
            <JobType xsi:type="log:JobType">PushtoSFTPServer</JobType>
            <TimeZone/>
            <RelText xsi:type="log:RelText">{units}</RelText>
            <RelTime xsi:type="xsd:byte">{duration}</RelTime>
            <Port xsi:type="xsd:byte">22</Port>
            <IPAddress xsi:type="xsd:string">{sftpserver}</IPAddress>
            <UserName xsi:type="xsd:string">{sftpuser}</UserName>
            <Password xsi:type="xsd:string">{sftppassword}</Password>
            <ZipInfo xsi:type="xsd:boolean">False</ZipInfo>
            <RemoteFolder xsi:type="xsd:string">sftpuser/s3</RemoteFolder>
            </soap:FileSelectionCriteria>
            </soap:SelectLogFiles>
            </soapenv:Body>
            </soapenv:Envelope>\
            '''
        res = requests.request("POST", self.cucmurl, data=payload, headers=headers, verify=False)
        print(res.text)
        xml_response = unescape(res.text)
        #print(xml_response)
        tags = self.between_two_tags(s=xml_response,sub1='<item xsi:type="ns2:file"><name xsi:type="xsd:string">',sub2='</name>')
        tags = list(filter(None, tags))
        for i, tag in enumerate(tags):
            if tag:
                print('tag: '+tag)
                # links = self.get_url_paths(url, ext, tag)
                # print(links[-1])
                # urllib.request.urlretrieve(links[-1],tag)
                # if tag.endswith('.gz'):
                #     print('ends with .gz')
                #     uncompressed = tag[:-3]
                #     print(uncompressed)
                #     command = 'zcat < '+tag+' > '+tag[:-3]
                #     subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
                #     tags[i] = tag[:-3]
                # elif tag.endswith('.gzo'):
                #     uncompressed = tag[:-4]
                #     print('ends in gzo')
                #     print(uncompressed)
                #     command = 'zcat < '+tag+' > '+tag[:-4]
                #     subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
                #     tags[i] = tag[:-4]
                    
                #TODO: ''' remove file from server to speed up finding '''
                #TODO: ''' keep the server running on reboot: python -m http.server '''
                #TODO: ''' uncompress the file before sending, closing gzo files '''
                #TODO: ''' zcat SDL001_100_001060.txt.gzo > SDL001_100_001060.txt '''
        print(tags)
        return tags
            # for res in result:
            #     print(res)
            #     if len(res) > 0:
            #         print(res)
            # print(tag)



'''
Service ( LogCollectionPortTypeService ) tns="http://schemas.cisco.com/ast/soap"
   Prefixes (1)
      ns0 = "http://schemas.cisco.com/ast/soap"
   Ports (1):
      (LogCollectionPort)
         Methods (4):
            GetOneFile(xs:string FileName)
            getTimeZone(xs:string LocalHost)
            listNodeServiceLogs()
            selectLogFiles(SchemaFileSelectionCriteria FileSelectionCriteria)
         Types (17):
            ArrayOfFile
            ArrayOfSchedule
            ArrayOfServiceLog
            ArrayOfServiceLogs
            ArrayOfSystemLog
            File
            Frequency
            JobType
            ListRequest
            Node
            NodeServiceLogList
            RelText
            ResultSet
            Schedule
            SchemaFileSelectionCriteria
            SchemaFileSelectionResult
            ServiceLogs
'''