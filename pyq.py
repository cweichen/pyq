"""
pyq.py

pyq (pronounce "pi queue") is a python client for accessing the Gracenote
Video API, which can retrieve TV providers, channels, and programs.

You will need a Gracenote client ID to use this module. See
developer.gracenote.com for more info.
"""

import xml.etree.ElementTree, urllib2, urllib, json

# Set DEBUG to True if you want this module to print out the query and response XML
DEBUG = False

class gn_provider(dict):
  """
  this class is a dict containing metadata for a GN provider
  """
  def __init__(self):
    self['id'] = ''
    self['name'] = ''
    self['place'] = ''
    self['provider_type']= ''

class gn_tvchannel(dict):
  """
  this class is a dict containing metadata for a GN tv channel
  """
  def __init__(self):
    self['id'] = ''
    self['name'] = ''
    self['name_short'] = ''
    self['channel_num'] = ''
    self['rank'] = 0

class gn_tvprogram(dict):
  """
  this class is a dict containing metadata for a GN tv program
  """
  def __init__(self):
    for k in ['id','title','title_sub','listing','episode_num',
              'season_num','epg_production_type','rank','groupref']:
      self[k] = ''

    self['ipgcategory'] = []

def register(clientID):
  """
  This function registers an application as a user of the Gracenote service
  
  It takes as a parameter a clientID string in the form of 
  "NNNNNNN-NNNNNNNNNNNNNNNNNNNNNNNNNNNNNNN" and returns a userID in a 
  similar format.
  
  As the quota of number of users (installed applications or devices) is 
  typically much lower than the number of queries, best practices are for a
  given installed application to call this only once, store the UserID in 
  persistent storage (e.g. filesystem), and then use these IDs for all 
  subsequent calls to the service.
  """
  
  # Create XML request
  query = _gnquery()
  query.addQuery('REGISTER')
  query.addQueryClient(clientID)
  
  queryXML = query.toString()
  
  # POST query
  response = urllib2.urlopen(_gnurl(clientID), queryXML)
  responseXML = response.read()
  
  # Parse response
  responseTree = xml.etree.ElementTree.fromstring(responseXML)
  
  responseElem = responseTree.find('RESPONSE')
  if responseElem.attrib['STATUS'] == 'OK':
    userElem = responseElem.find('USER')
    userID = userElem.text
  
  return userID
  
class _gnquery:
  """
  A utility class for creating and configuring an XML query for POST'ing to
  the Gracenote service
  """

  def __init__(self):
    self.root = xml.etree.ElementTree.Element('QUERIES')
    
  def addAuth(self, clientID, userID):
    auth = xml.etree.ElementTree.SubElement(self.root, 'AUTH')
    client = xml.etree.ElementTree.SubElement(auth, 'CLIENT')
    user = xml.etree.ElementTree.SubElement(auth, 'USER')
  
    client.text = clientID
    user.text = userID

  def addLang(self,lang='eng'):
    xlang = xml.etree.ElementTree.SubElement(self.root,'LANG')
    xlang.text = lang

  def addCountry(self,country='usa'):
    xcountry = xml.etree.ElementTree.SubElement(self.root,'COUNTRY')
    xcountry.text = country
  
  def addQuery(self, cmd):
    query = xml.etree.ElementTree.SubElement(self.root, 'QUERY')
    query.attrib['CMD'] = cmd

  def toString(self):
    return xml.etree.ElementTree.tostring(self.root)

def _gnurl(clientID):
  """
  Helper function to form URL to Gracenote service
  """
  clientIDprefix = clientID.split('-')[0]
  return 'https://c' + clientIDprefix + '.web.cddbp.net/webapi/xml/1.0/'

def _prn_xml(xml_str,is_query=True):
  """
  prints out xml string for debugging
  """
  print '------------'
  if is_query:
    print 'QUERY XML'
  else:
    print 'RESPONSE XML'
  print '------------'
  print xml_str
  
def searchProviders(clientID, userID, zipcode):
  """
  Queries the Gracenote service for a list of TV providers for the given zip
  code
  """

  if not isinstance(zipcode,str):
    zipcode = str(zipcode)
  
  # Create XML request
  query = _gnquery()
  query.addAuth(clientID, userID)
  query.addLang()
  query.addCountry()
  query.addQuery('TVPROVIDER_LOOKUP')
  
  query_elm = query.root.find('QUERY')
  zip_tag = xml.etree.ElementTree.SubElement(query_elm,'POSTALCODE')
  zip_tag.text = zipcode
  
  queryXML = query.toString()

  DEBUG=1

  if DEBUG:
    _prn_xml(queryXML,is_query=True)
  
  # POST query
  response = urllib2.urlopen(_gnurl(clientID), queryXML)
  responseXML = response.read()
  
  if DEBUG:
    _prn_xml(responseXML,is_query=False)

  response_tree = xml.etree.ElementTree.fromstring(responseXML)
  return response_tree


def _etree_to_dict(t):
  if t.getchildren():
    d = {t.tag : map(_etree_to_dict, t.getchildren())}
  else:
    d = {t.tag : t.text}

  return d
