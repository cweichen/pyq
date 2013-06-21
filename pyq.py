"""
pyq.py

pyq (pronounced "pie Q") is a python client for accessing the Gracenote
eyeQ API, which can retrieve TV providers, channels, and programs.

You will need a Gracenote client ID to use this module. See
developer.gracenote.com for more info.
"""

import xml.etree.ElementTree, urllib2, urllib, json, HTMLParser

htmlparser = HTMLParser.HTMLParser()

# Set DEBUG to True if you want this module to print out the query and response XML
DEBUG = True

class gn_provider(dict):
  """
  this class is a dict containing metadata for a GN provider
  """
  def __init__(self):
    self['id'] = ''
    self['name'] = ''
    self['place'] = ''
    self['type']= ''

class gn_channel(dict):
  """
  this class is a dict containing metadata for a GN tv channel
  """
  def __init__(self):
    self['id'] = ''
    self['name'] = ''
    self['name_short'] = ''
    self['num'] = ''
    self['rank'] = 0
    self['logo_url'] = ''

class gn_program(dict):
  """
  this class is a dict containing metadata for a GN tv program
  """
  def __init__(self):
    for k in ['id','title','title_sub','listing','episode_num',
              'season_num','epgproduction_type','rank','groupref',
              'image_url','ipgcategory_image_url']:
      self[k] = ''

    self['ipgcategories'] = []

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

  def addQueryMode(self, modeStr):
    query = self.root.find('QUERY')
    mode = xml.etree.ElementTree.SubElement(query, 'MODE')
    mode.text = modeStr

  def addQueryTextField(self, fieldName, value):
    query = self.root.find('QUERY')
    text = xml.etree.ElementTree.SubElement(query, 'TEXT')
    text.attrib['TYPE'] = fieldName
    text.text = value

  def addQueryOption(self, parameterName, value):
    query = self.root.find('QUERY')
    option = xml.etree.ElementTree.SubElement(query, 'OPTION')
    parameter = xml.etree.ElementTree.SubElement(option, 'PARAMETER')
    parameter.text = parameterName
    valueElem = xml.etree.ElementTree.SubElement(option, 'VALUE')
    valueElem.text = value

  def addQueryGNID(self, GNID):
    query = self.root.find('QUERY')
    GNIDElem = xml.etree.ElementTree.SubElement(query, 'GN_ID')
    GNIDElem.text = GNID

  def addQueryClient(self, clientID):
    query = self.root.find('QUERY')
    client = xml.etree.ElementTree.SubElement(query, 'CLIENT')
    client.text = clientID

  def addQueryTVChannels(self, channelIDs):
    if type(channelIDs) is not list: channelIDs = [channelIDs]
    query = self.root.find('QUERY')
    tvchannel = xml.etree.ElementTree.SubElement(query, 'TVCHANNEL')
    for channelID in channelIDs:
      gn_id = xml.etree.ElementTree.SubElement(tvchannel, 'GN_ID')
      gn_id.text = channelID

  def addQueryCustomNode(self, nodeName, nodeText, attribName=None, attribValue=None):
    query = self.root.find('QUERY')
    node = xml.etree.ElementTree.SubElement(query, nodeName)
    node.text = nodeText
    if attribName and attribValue:
      node.attrib[attribName] = attribValue

  def toString(self):
    return xml.etree.ElementTree.tostring(self.root)

def _gnurl(clientID):
  """
  Helper function to form URL to Gracenote service
  """
  clientIDprefix = clientID.split('-')[0]
  return 'https://c' + clientIDprefix + '.ipg.web.cddbp.net/webapi/xml/1.0/'

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
  
def lookupProviders(clientID, userID, zipcode):
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
  
  _gnquery.addQueryCustomNode(query, 'POSTALCODE', zipcode)
  
  queryXML = query.toString()

  if DEBUG:
    _prn_xml(queryXML,is_query=True)
  
  # POST query
  response = urllib2.urlopen(_gnurl(clientID), queryXML)
  responseXML = response.read()
  
  if DEBUG:
    _prn_xml(responseXML,is_query=False)

  # Create array of all TV providers
  providers = []

  # Parse response XML
  response_tree = xml.etree.ElementTree.fromstring(responseXML)
  responseElem = response_tree.find('RESPONSE')
  
  if responseElem.attrib['STATUS'] == 'OK':
    for tvproviderElem in responseElem.iter('TVPROVIDER'):
      
      # Create gn_provider object
      provider = gn_provider()

      # Parse TV Provider fields
      provider['id'] =  _getElemText(tvproviderElem, "GN_ID")
      provider['name'] = _getElemText(tvproviderElem, "NAME")
      provider['place'] = _getElemText(tvproviderElem, "PLACE")
      provider['type'] = _getElemText(tvproviderElem, "PROVIDERTYPE")
      providers.append(provider)
  
  return providers

def lookupChannels(clientID, userID, providerID):
  """ 
  Queries the Gracenote service for the list of channels offered by
  that provider
  """
  # Create XML request
  query = _gnquery()
  query.addAuth(clientID, userID)
  query.addLang()
  query.addCountry()
  query.addQuery('TVCHANNEL_LOOKUP')
  
  _gnquery.addQueryMode(query, 'TVPROVIDER')
  _gnquery.addQueryCustomNode(query, 'GN_ID', providerID)
  _gnquery.addQueryOption(query, 'SELECT_EXTENDED', 'IMAGE') # Get channel logos
  queryXML = query.toString()

  if DEBUG:
    _prn_xml(queryXML,is_query=True)
  
  # POST query
  response = urllib2.urlopen(_gnurl(clientID), queryXML)
  responseXML = response.read()
  
  if DEBUG:
    _prn_xml(responseXML,is_query=False)

  # Create array of all channels
  channels = []

  # Parse response XML
  response_tree = xml.etree.ElementTree.fromstring(responseXML)
  responseElem = response_tree.find('RESPONSE')
  
  if responseElem.attrib['STATUS'] == 'OK':
    for tvchannelElem in responseElem.iter('TVCHANNEL'):
      
      # Create gn_channel object
      channel = gn_channel()

      # Parse TV Channel fields
      channel['id'] =  _getElemText(tvchannelElem, "GN_ID")
      channel['name'] = _getElemText(tvchannelElem, "NAME")
      channel['name_short'] = _getElemText(tvchannelElem, "NAME_SHORT")
      channel['num'] = _getElemText(tvchannelElem, "CHANNEL_NUM")
      channel['rank'] = _getElemText(tvchannelElem, "RANK")
      channel['logo_url'] = htmlparser.unescape(_getElemText(tvchannelElem, 'URL', 'TYPE', 'IMAGE'))
      channels.append(channel)
  
  return channels

def lookupProgramsByChannels(clientID, userID, channelIDs, startDateTime=None, endDateTime=None):
  """ 
  Queries the Gracenote service for the list of programs airing on
  a set of channels, during a specified time window
  """

  # We expect channelIDs to be a list of strings. 
  # If channelIDs is a single string, create a list of one string
  if type(channelIDs) is not list: channelIDs = [channelIDs]

  # Create XML request
  query = _gnquery()
  query.addAuth(clientID, userID)
  query.addLang()
  query.addCountry()
  query.addQuery('TVGRID_LOOKUP')
  
  _gnquery.addQueryTVChannels(query, channelIDs)
  if startDateTime and endDateTime:
    _gnquery.addQueryCustomNode(query, 'DATE', startDateTime, 'TYPE', 'START')
    _gnquery.addQueryCustomNode(query, 'DATE', endDateTime, 'TYPE', 'END')
  _gnquery.addQueryOption(query, 'SELECT_EXTENDED', 'TVPROGRAM_IMAGE,IPGCATEGORY_IMAGE') # Get channel logos
  
  queryXML = query.toString()

  if DEBUG:
    _prn_xml(queryXML,is_query=True)
  
  # POST query
  response = urllib2.urlopen(_gnurl(clientID), queryXML)
  responseXML = response.read()
  
  if DEBUG:
    _prn_xml(responseXML,is_query=False)

  # Create array of all programs
  programs = []

  # Parse response XML
  response_tree = xml.etree.ElementTree.fromstring(responseXML)
  responseElem = response_tree.find('RESPONSE')
  
  if responseElem.attrib['STATUS'] == 'OK':
    for tvprogramElem in responseElem.iter('TVPROGRAM'):
      
      # Create gn_program object
      program = gn_program()

      # Parse TV Program fields
      program['id'] =  _getElemText(tvprogramElem, "GN_ID")
      program['title'] = _getElemText(tvprogramElem, "TITLE")
      program['title_sub'] = _getElemText(tvprogramElem, "TITLE_SUB")
      program['listing'] = _getElemText(tvprogramElem, "LISTING")
      program['episode_num'] = _getElemText(tvprogramElem, "EPISODE_NUM")
      program['season_num'] = _getElemText(tvprogramElem, "SEASON_NUM")
      program['epgproduction_type'] = _getElemText(tvprogramElem, "EPGPRODUCTION_TYPE")
      program['rank'] = _getElemText(tvprogramElem, "RANK")
      program['groupref'] = _getElemText(tvprogramElem, "GROUPREF")
      program['image_url'] = htmlparser.unescape(_getElemText(tvprogramElem, 'URL', 'TYPE', 'IMAGE'))
      program['ipgcategory_image_url'] = htmlparser.unescape(_getElemText(tvprogramElem, 'URL', 'TYPE', 'IPGCATEGORY_IMAGE'))
      for ipgcategoryElem in tvprogramElem.iter('IPGCATEGORY'):
        program['ipgcategories'].append({'ipgcategory_l1': _getElemText(ipgcategoryElem, "IPGCATEGORY_L1"),
                                    'ipgcategory_l2': _getElemText(ipgcategoryElem, "IPGCATEGORY_L2")})
      programs.append(program)
  
  return programs

def _getElemText(parentElem, elemName, elemAttribName=None, elemAttribValue=None):
  """
  XML parsing helper function to find child element with a specific name, 
  and return the text value
  """
  elems = parentElem.findall(elemName)
  for elem in elems:
    if elemAttribName is not None and elemAttribValue is not None:
      if elem.attrib[elemAttribName] == elemAttribValue:
        return urllib.unquote(elem.text)
      else:
        continue
    else: # Just return the first one
      return urllib.unquote(elem.text)
  return ''

def _getElemAttrib(parentElem, elemName, elemAttribName):
  """
  XML parsing helper function to find child element with a specific name, 
  and return the value of a specified attribute
  """
  elem = parentElem.find(elemName)
  if elem is not None:
    return elem.attrib[elemAttribName]

def _getMultiElemText(parentElem, elemName, topKey, bottomKey):
  """
  XML parsing helper function to return a 2-level dict of multiple elements
  by a specified name, using topKey as the first key, and bottomKey as the second key
  """
  elems = parentElem.findall(elemName)
  result = {} # 2-level dictionary of items, keyed by topKey and then bottomKey
  if elems is not None:
    for elem in elems:
      if topKey in elem.attrib:
        result[elem.attrib[topKey]] = {bottomKey:elem.attrib[bottomKey], 'TEXT':elem.text}
      else:
        result['0'] = {bottomKey:elem.attrib[bottomKey], 'TEXT':elem.text}
  return result

def _etree_to_dict(t):
  if t.getchildren():
    d = {t.tag : map(_etree_to_dict, t.getchildren())}
  else:
    d = {t.tag : t.text}

  return d
