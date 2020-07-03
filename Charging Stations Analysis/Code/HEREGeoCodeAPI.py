# -*- coding: utf-8 -*-
"""
Created on Mon Oct  7 11:42:49 2019

@author: EEANNNG

HERE Maps GeoCoding API - 250K Transactions per month FREE
Project: https://developer.here.com/projects/PROD-7accb716-d5d0-4b49-8fdd-e5b88c05d64c
GeoCoding docs: https://developer.here.com/api-explorer/rest/batch_geocoding/batch-geocode-addresses

"""

def run_HERE_API(folder,address_file):
    import requests
    # Batch geocoding of many addresses, save it in a CSV (tab delimited = "%09" = "/t")
    # Ensure headers are "recId", "searchText", "country" -> "recId" is the only possible identifier in the results returned, so make sure it is unique.
    filepath = folder + address_file
    url = "https://batch.geocoder.api.here.com/6.2/jobs?gen=8&app_id=fXKBafPTDSTKrZG7PRob&app_code=iprgBFN-XF1xan19GJQKrQ&action=run&mailto=eeann.ng%40gmail.com&header=true&indelim=%09&outdelim=%09&outcols=displayLatitude%2CdisplayLongitude%2ClocationLabel%2ChouseNumber%2Cstreet%2Cdistrict%2Ccity%2CpostalCode%2Ccounty%2Cstate%2Ccountry&outputCombined=false"
    with open(filepath,encoding='utf-8') as fh:
        mydata = fh.read().replace('ï»¿',"").encode('utf-8')
        response = requests.post(url, data=mydata)
    return response
        
def checkStatus_HERE_API(folder,response):
    import requests, zipfile, io
    import xml.etree.ElementTree as ET
    # Check status 
    responseXml = ET.fromstring(response.content)
    requestID = responseXml.find('Response').find('MetaInfo').find('RequestId').text
    url = "https://batch.geocoder.api.here.com/6.2/jobs/"+requestID+"?action=status&app_id=fXKBafPTDSTKrZG7PRob&app_code=iprgBFN-XF1xan19GJQKrQ"
    r = requests.get(url)
    responseXml = ET.fromstring(r.content)
    status = responseXml.find('Response').find('Status').text
    print('Status :',status)
    print('TotalCount :',responseXml.find('Response').find('TotalCount').text)
    print('ValidCount :',responseXml.find('Response').find('ValidCount').text)
    print('InvalidCount :',responseXml.find('Response').find('InvalidCount').text)
    print('ProcessedCount :',responseXml.find('Response').find('ProcessedCount').text)
    print('PendingCount :',responseXml.find('Response').find('PendingCount').text)
    print('SuccessCount :',responseXml.find('Response').find('SuccessCount').text)
    print('ErrorCount :',responseXml.find('Response').find('ErrorCount').text)
    
    # Get batch results
    if status == 'completed':
        r = requests.get("https://batch.geocoder.api.here.com/6.2/jobs/"+requestID+"/result?app_id=fXKBafPTDSTKrZG7PRob&app_code=iprgBFN-XF1xan19GJQKrQ",headers={'Content-Type':'application/octet-stream'}, stream=True)
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall(folder)





