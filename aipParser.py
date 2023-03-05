##################################################################
#
# Python script to parse the following locals:
#    BE - Belgium
#    FI - Finland
#    FR - France
#    IE - Ireland
#    NL - Netherlands
#    NO - Norway
#    RU - Russia
#    SE - Sweden
#    UK - United Kingdom
# AIP sites and generate a JSON file that can be used by eBAG in
# X-Plane 11, to view the PDF chart files for AIP info.
#
# Only tested with Python 3.8.
#
# Required modules to install to get this to work:
#   pip install BeautifulSoup
#
# Example run lines:
#   python aipParser.py --region BE
#   python aipParser.py --region ES
#   python aipParser.py --region FI
#   python aipParser.py --region FR
#   python aipParser.py --region IE
#   python aipParser.py --region NO --previous
#   python aipParser.py --region NL
#   python aipParser.py --region RU
#   python aipParser.py --region SE
#   python aipParser.py --region UK
#   python aipParser.py --region UK --debug --previous --codesort
#
##################################################################

import argparse
import datetime
import logging
import traceback
import ssl
import urllib.error
from urllib.request import urlopen, Request

from bs4 import BeautifulSoup

# AIP schedule gotten from:
#   https://nats-uk.ead-it.com/cms-nats/export/sites/default/en/Publications/publication-schedule/10-year-AIRAC.pdf
# remember when you remove dates you need to alter the offset for NO and ES
# AIRAC Number, SPONSOR Change Requests CUTOFF, AMDT PUBLISHED, AIRAC EFFECTIVE DATE
effectiveDates = [
    [ "AIRAC 01/2022", "2021-10-29", "2021-12-16", "2022-01-27" ],
    [ "AIRAC 02/2022", "2021-11-26", "2022-01-13", "2022-02-24" ],
    [ "AIRAC 03/2022", "2021-12-17", "2022-02-10", "2022-03-24" ],
    [ "AIRAC 04/2022", "2022-01-21", "2022-03-10", "2022-04-21" ],
    [ "AIRAC 05/2022", "2022-02-18", "2022-04-07", "2022-05-19" ],
    [ "AIRAC 06/2022", "2022-03-18", "2022-05-05", "2022-06-16" ],
    [ "AIRAC 07/2022", "2022-04-15", "2022-06-02", "2022-07-14" ],
    [ "AIRAC 08/2022", "2022-05-13", "2022-06-30", "2022-08-11" ],
    [ "AIRAC 09/2022", "2022-06-10", "2022-07-28", "2022-09-08" ],
    [ "AIRAC 10/2022", "2022-07-08", "2022-08-25", "2022-10-06" ],
    [ "AIRAC 11/2022", "2022-08-05", "2022-09-22", "2022-11-03" ],
    [ "AIRAC 12/2022", "2022-09-02", "2022-10-20", "2022-12-01" ],
    [ "AIRAC 13/2022", "2022-09-30", "2022-11-17", "2022-12-29" ],
    [ "AIRAC 01/2023", "2022-10-28", "2022-12-15", "2023-01-26" ],
    [ "AIRAC 02/2023", "2022-11-25", "2023-01-12", "2023-02-23" ],
    [ "AIRAC 03/2023", "2022-12-16", "2023-02-09", "2023-03-23" ],
    [ "AIRAC 04/2023", "2023-01-20", "2023-03-09", "2023-04-20" ],
    [ "AIRAC 05/2023", "2023-02-17", "2023-04-06", "2023-05-18" ],
    [ "AIRAC 06/2023", "2023-03-17", "2023-05-04", "2023-06-15" ],
    [ "AIRAC 07/2023", "2023-04-14", "2023-06-01", "2023-07-13" ],
    [ "AIRAC 08/2023", "2023-05-12", "2023-06-29", "2023-08-10" ],
    [ "AIRAC 09/2023", "2023-06-09", "2023-07-27", "2023-09-07" ],
    [ "AIRAC 10/2023", "2023-07-07", "2023-08-24", "2023-10-05" ],
    [ "AIRAC 11/2023", "2023-08-04", "2023-09-21", "2023-11-02" ],
    [ "AIRAC 12/2023", "2023-09-01", "2023-10-19", "2023-11-30" ],
    [ "AIRAC 13/2023", "2023-09-29", "2023-11-16", "2023-12-28" ],
    [ "AIRAC 01/2024", "2023-10-27", "2023-12-14", "2024-01-25" ],
    [ "AIRAC 02/2024", "2023-11-24", "2024-01-11", "2024-02-22" ],
    [ "AIRAC 03/2024", "2023-12-22", "2024-02-08", "2024-03-21" ],
    [ "AIRAC 04/2024", "2024-01-19", "2024-03-07", "2024-04-18" ],
    [ "AIRAC 05/2024", "2024-02-16", "2024-04-04", "2024-05-16" ],
    [ "AIRAC 06/2024", "2024-03-15", "2024-05-02", "2024-06-13" ],
    [ "AIRAC 07/2024", "2024-04-12", "2024-05-30", "2024-07-11" ],
    [ "AIRAC 08/2024", "2024-05-10", "2024-06-27", "2024-08-08" ],
    [ "AIRAC 09/2024", "2024-06-07", "2024-07-25", "2024-09-05" ],
    [ "AIRAC 10/2024", "2024-07-05", "2024-08-22", "2024-10-03" ],
    [ "AIRAC 11/2024", "2024-08-02", "2024-09-19", "2024-10-31" ],
    [ "AIRAC 12/2024", "2024-08-30", "2024-10-17", "2024-11-28" ],
    [ "AIRAC 13/2024", "2024-09-27", "2024-11-14", "2024-12-26" ],
    [ "AIRAC 01/2025", "2024-10-25", "2024-12-12", "2025-01-23" ],
    [ "AIRAC 02/2025", "2024-11-22", "2025-01-09", "2025-02-20" ],
    [ "AIRAC 03/2025", "2024-12-20", "2025-02-06", "2025-03-20" ],
    [ "AIRAC 04/2025", "2025-01-17", "2025-03-06", "2025-04-17" ],
    [ "AIRAC 05/2025", "2025-02-14", "2025-04-03", "2025-05-15" ],
    [ "AIRAC 06/2025", "2025-03-14", "2025-05-01", "2025-06-12" ],
    [ "AIRAC 07/2025", "2025-04-11", "2025-05-29", "2025-07-10" ],
    [ "AIRAC 08/2025", "2025-05-09", "2025-06-26", "2025-08-07" ],
    [ "AIRAC 09/2025", "2025-06-06", "2025-07-24", "2025-09-04" ],
    [ "AIRAC 10/2025", "2025-07-04", "2025-08-21", "2025-10-02" ],
    [ "AIRAC 11/2025", "2025-08-01", "2025-09-18", "2025-10-30" ],
    [ "AIRAC 12/2025", "2025-08-29", "2025-10-16", "2025-11-27" ],
    [ "AIRAC 13/2025", "2025-09-26", "2025-11-13", "2025-12-25" ],
    [ "AIRAC 01/2026", "2025-10-24", "2025-12-11", "2026-01-22" ],
    [ "AIRAC 02/2026", "2025-11-21", "2026-01-08", "2026-02-19" ],
    [ "AIRAC 03/2026", "2025-12-19", "2026-02-05", "2026-03-19" ],
    [ "AIRAC 04/2026", "2026-01-16", "2026-03-05", "2026-04-16" ],
    [ "AIRAC 05/2026", "2026-02-13", "2026-04-02", "2026-05-14" ],
    [ "AIRAC 06/2026", "2026-03-13", "2026-04-30", "2026-06-11" ],
    [ "AIRAC 07/2026", "2026-04-10", "2026-05-28", "2026-07-09" ],
    [ "AIRAC 08/2026", "2026-05-08", "2026-06-25", "2026-08-06" ],
    [ "AIRAC 09/2026", "2026-06-05", "2026-07-23", "2026-09-03" ],
    [ "AIRAC 10/2026", "2026-07-03", "2026-08-20", "2026-10-01" ],
    [ "AIRAC 11/2026", "2026-07-31", "2026-09-17", "2026-10-29" ],
    [ "AIRAC 12/2026", "2026-08-28", "2026-10-15", "2026-11-26" ],
    [ "AIRAC 13/2026", "2026-09-25", "2026-11-12", "2026-12-24" ],
    [ "AIRAC 01/2027", "2026-10-23", "2026-12-10", "2027-01-21" ],
    [ "AIRAC 02/2027", "2026-11-20", "2027-01-07", "2027-02-18" ],
    [ "AIRAC 03/2027", "2026-12-18", "2027-02-04", "2027-03-18" ],
    [ "AIRAC 04/2027", "2027-01-15", "2027-03-04", "2027-04-15" ],
    [ "AIRAC 05/2027", "2027-02-12", "2027-04-01", "2027-05-13" ],
    [ "AIRAC 06/2027", "2027-03-12", "2027-04-29", "2027-06-10" ],
    [ "AIRAC 07/2027", "2027-04-09", "2027-05-27", "2027-07-08" ],
    [ "AIRAC 08/2027", "2027-05-07", "2027-06-24", "2027-08-05" ],
    [ "AIRAC 09/2027", "2027-06-04", "2027-07-22", "2027-09-02" ],
    [ "AIRAC 10/2027", "2027-07-02", "2027-08-19", "2027-09-30" ],
    [ "AIRAC 11/2027", "2027-07-30", "2027-09-16", "2027-10-28" ],
    [ "AIRAC 12/2027", "2027-08-27", "2027-10-14", "2027-11-25" ],
    [ "AIRAC 13/2027", "2027-09-24", "2027-11-11", "2027-12-23" ],
    [ "AIRAC 01/2028", "2027-10-22", "2027-12-09", "2028-01-20" ],
    [ "AIRAC 02/2028", "2027-11-19", "2028-01-06", "2028-02-17" ],
    [ "AIRAC 03/2028", "2027-12-17", "2028-02-03", "2028-03-16" ],
    [ "AIRAC 04/2028", "2028-01-14", "2028-03-02", "2028-04-13" ],
    [ "AIRAC 05/2028", "2028-02-11", "2028-03-30", "2028-05-11" ],
    [ "AIRAC 06/2028", "2028-03-10", "2028-04-27", "2028-06-08" ],
    [ "AIRAC 07/2028", "2028-04-07", "2028-05-25", "2028-07-06" ],
    [ "AIRAC 08/2028", "2028-05-05", "2028-06-22", "2028-08-03" ],
    [ "AIRAC 09/2028", "2028-06-02", "2028-07-20", "2028-08-31" ],
    [ "AIRAC 10/2028", "2028-06-30", "2028-08-17", "2028-09-28" ],
    [ "AIRAC 11/2028", "2028-07-28", "2028-09-14", "2028-10-26" ],
    [ "AIRAC 12/2028", "2028-08-25", "2028-10-12", "2028-11-23" ],
    [ "AIRAC 13/2028", "2028-09-22", "2028-11-09", "2028-12-21" ],
    [ "AIRAC 01/2029", "2028-10-20", "2028-12-07", "2029-01-18" ],
    [ "AIRAC 02/2029", "2028-11-17", "2029-01-04", "2029-02-15" ],
    [ "AIRAC 03/2029", "2028-12-15", "2029-02-01", "2029-03-15" ],
    [ "AIRAC 04/2029", "2029-01-12", "2029-03-01", "2029-04-12" ],
    [ "AIRAC 05/2029", "2029-02-09", "2029-03-29", "2029-05-10" ],
    [ "AIRAC 06/2029", "2029-03-09", "2029-04-26", "2029-06-07" ],
    [ "AIRAC 07/2029", "2029-04-06", "2029-05-24", "2029-07-05" ],
    [ "AIRAC 08/2029", "2029-05-04", "2029-06-21", "2029-08-02" ],
    [ "AIRAC 09/2029", "2029-06-01", "2029-07-19", "2029-08-30" ],
    [ "AIRAC 10/2029", "2029-06-29", "2029-08-16", "2029-09-27" ],
    [ "AIRAC 11/2029", "2029-07-27", "2029-09-13", "2029-10-25" ],
    [ "AIRAC 12/2029", "2029-08-24", "2029-10-11", "2029-11-22" ],
    [ "AIRAC 13/2029", "2029-09-21", "2029-11-08", "2029-12-20" ],
    [ "AIRAC 01/2030", "2029-10-19", "2029-12-06", "2030-01-17" ],
    [ "AIRAC 02/2030", "2029-11-16", "2030-01-03", "2030-02-14" ],
    [ "AIRAC 03/2030", "2029-12-14", "2030-01-31", "2030-03-14" ],
    [ "AIRAC 04/2030", "2030-01-11", "2030-02-28", "2030-04-11" ],
    [ "AIRAC 05/2030", "2030-02-08", "2030-03-28", "2030-05-09" ],
    [ "AIRAC 06/2030", "2030-03-08", "2030-04-25", "2030-06-06" ],
    [ "AIRAC 07/2030", "2030-04-05", "2030-05-23", "2030-07-04" ],
    [ "AIRAC 08/2030", "2030-05-03", "2030-06-20", "2030-08-01" ],
    [ "AIRAC 09/2030", "2030-05-31", "2030-07-18", "2030-08-29" ],
    [ "AIRAC 10/2030", "2030-06-28", "2030-08-15", "2030-09-26" ],
    [ "AIRAC 11/2030", "2030-07-26", "2030-09-12", "2030-10-24" ],
    [ "AIRAC 12/2030", "2030-08-23", "2030-10-10", "2030-11-21" ],
    [ "AIRAC 13/2030", "2030-09-20", "2030-11-07", "2030-12-19" ]
]

# hold all the website information
aipInformation = {
    "BE": ["Belgium",   "https://ops.skeyes.be/html/belgocontrol_static"],
    "ES": ["Spain",     "https://aip.enaire.es"],
    "FI": ["Finland",   "https://ais.fi"],
    "FR": ["France",    "https://www.sia.aviation-civile.gouv.fr/dvd"],
    "IE": ["Ireland",   "http://iaip.iaa.ie"],
    "NL": ["Netherlands", "https://eaip.lvnl.nl"],
    "NO": ["Norway",    "https://ais.avinor.no/no"],
    "RU": ["Russia",    "http://www.caiga.ru"],
    "SE": ["Sweden",    "https://aro.lfv.se"],
    "UK": ["UK",        "https://www.aurora.nats.co.uk/htmlAIP/Publications"]
}

# setup the file logger
logger = logging.getLogger("aipParser")
logging.basicConfig(level=logging.INFO,
                    format = u"%(asctime)s: %(levelname)-8s: %(message)s", 
                    datefmt = "%Y-%m-%d %H:%M:%S",
                    handlers=[logging.FileHandler("aipParser.log", "w", "utf-8")])

# setup the console logger
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("%(levelname)-8s: %(message)s")
console.setFormatter(formatter)
logging.getLogger("aipParser").addHandler(console)

# set up what user agent we want to mimic, as some site block
# unknown agent types
#header_user_agent="Mozilla/5.0"
header_user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.1 Safari/603.1.30"

# define what section headers we want
adType2 = "AD 2 AERODROMES"
adType3 = "AD 3 HELIPORT"

# structure to hold the page data
aipPages = {
    adType2 : {},
    adType3 : {}
}

# default sort order is either NAME or CODE
# if its NAME then in the JSON we output NAME : CODE
# if its NAME then in the JSON we output CODE : NAME
sortOrder = "NAME"


#
# Common routine to add to the AIP page data structure
#
def addAipPage (adType, dromeCode, dromeName, dromeHref, ignoreDups = False):
    global aipPages, sortOrder
    key = ""

    # check what order we want to store data
    if sortOrder == "NAME":
        key = dromeName
    else:
        key = dromeCode

    # check its a known type
    if adType not in aipPages.keys():
        logger.info ("    Unknown AD type found [{0}] for [{1}]. Ignoring.".format(adType, key))
        return

    if key not in aipPages[adType].keys():
        dromeStructure = {
                            "Name" : dromeName,
                            "Code" : dromeCode,
                            "PageURL" : dromeHref,
                            "PageLinks" : {}
                         }
        aipPages[adType][key] = dromeStructure
    else:
        if not ignoreDups:
            logger.info ("    Duplicate [{0}] found [{1}] for AD type [{2}]. Ignoring.".format(sortOrder, key, adType))
        return

    logger.debug ("    {0} == {1} == {2} == {3}".format(adType, dromeCode, dromeName, dromeHref))

    return


#
# Common routine to update the page links data in the AIP page data structure
#
def updateAipPageLinks (adType, dromeCode, dromeName, dromeLinks):
    global aipPages, sortOrder
    key = ""

    # check what order we want to store data
    if sortOrder == "NAME":
        key = dromeName
    else:
        key = dromeCode

    # check its a known type
    if adType not in aipPages.keys():
        logger.info ("    Unknown AD type found [{0}] for [{1}]. Ignoring.".format(adType, key))
        return

    if key in aipPages[adType].keys():
        aipPages[adType][key]["PageLinks"] = dromeLinks
    else:
        logger.info ("    Unknown [{0}] found [{1}] for AD type [{2}]. Not adding links.".format(sortOrder, key, adType))
        return

    #logger.debug ("    {0} == {1} == {2} == {3}".format(adType, dromeCode, dromeName, dromeHref))

    return


#
# Common routine to load a webpage
#
def getWebPage ( pageType, pageName, pageURL, sslHack = False ):
    logger.info ("Parsing {0} {1} main page: {2}".format(pageName, pageType, pageURL))

    try:
        if sslHack:
            # main site has broken site certificate, so ignore ssl issues
            ssl._create_default_https_context = ssl._create_unverified_context

        # open up the main page and parse it
        page = urllib.request.urlopen(Request(pageURL, headers={"User-Agent": header_user_agent})).read()
    except urllib.error.HTTPError as e:
        logger.error ("HTTP Error {0}: {1}".format(e.code, e.reason))
        exit(1)
    except Exception as e:
        logger.error (traceback.format_exc())
        exit(1)

    html = BeautifulSoup(page, "html.parser")

    logger.debug ("    TITLE : " + html.title.string)
    #logger.debug ("    PAGE :\n{0}".format(html))

    return html


#
# parse the main BE AIP page to get list of Aerodromes and their
# associated information pages
#
def parseMainPageBE ( aipBaseUrl, aipRegion ):
    aipMainPage = "{0}/html/eAIP/EB-menu-en-GB.html".format(aipBaseUrl)

    # get site page
    html = getWebPage ( "Aip",  aipRegion, aipMainPage, True )

    # loop through all the link tags
    for link in html.find_all("a"):
        #logger.debug (link)
        type = ""
        title = ""
        href = ""
        id = ""
        code = ""
        name = link.get_text()[6:]
        if ("title" in link.attrs):
            title = link["title"]
        if ("href" in link.attrs):
            href = link["href"]
        if ("id" in link.attrs):
            id = link["id"]
            if ("AD-2." == id[:5]):
                type = adType2
            elif ("AD-3." == id[:5]):
                type = adType3

            if type not in ("", None):
                idSplit = id.split(".")
                if len(idSplit) == 2:
                    code = idSplit[1]

        #logger.debug (title + "==" + code + "==" + href + "==" + type)

        # check if this is a valid link we want
        if (title and href and code and type):
            new_href = aipBaseUrl + "/html/eAIP/" + href.replace("#" + id, "")
            addAipPage (type, code, name, new_href)
            parseDromePageBE (type, code, name, aipBaseUrl, new_href)

    return


#
# parse the main ES AIP page to get list of Aerodromes and their
# associated information pages
#
def parseMainPageES ( aipBaseUrl, aipRegion ):
    global aipPages

    aipMainPage = "{0}/AIP-es.html".format(aipBaseUrl)

    # get site page
    html = getWebPage ( "Aip",  aipRegion, aipMainPage )

    # for this site we need to keep track of the code
    # so we can look up the drome name
    dromeMapping = {}

    type = ""
    old_code = ""
    old_name = ""
    code = ""
    name = ""
    title = ""
    href = ""
    dromeDetail = False
    tmpPages = {}
    for item in html.find_all(["h1", "td"]):
        #logger.debug ("{0} == {1} == {2}".format(type, item.name, item))

        # try and find the section start
        if item.name == "h1":
            if item.get_text() == "AD 2":
                type = adType2
                dromeDetail = False
                continue
            elif item.get_text() == "AD 3":
                type = adType3
                dromeDetail = False
                old_code = ""
                continue
            else:
                if type not in ("", None):
                    dromeDetail = True
                    continue

        if type in ("", None):
            continue

        if item.name == "td" and not dromeDetail:
            if ("class" in item.attrs):
                if item["class"][0] == "id":
                    # some drome codes have xxxx/xxxx so ignore second part
                    code = item.get_text()[:4]
                elif item["class"][0] == "desc":
                    name = item.get_text()
            if (type and code and name):
                addAipPage(type, code, name, href)
                dromeMapping[code] = name
                code = ""
                name = ""

        if item.name == "td" and dromeDetail:
            if ("class" in item.attrs):
                if item["class"][0] == "id":
                    text = item.get_text()
                    code = text[5:9]

                    if ("onclick" in item.attrs):
                        onclick = item["onclick"]
                        if onclick.find(".pdf") >= 0:
                            href = "{0}/{1}".format(aipBaseUrl, onclick.split("\'")[1])
                        else:
                            code = ""
                            href = ""
                            title = ""
                if item["class"][0] == "desc" and code not in ("", None):
                    title = item.get_text().replace("&", "and")

            if (type and code and title and href):
                filename = code + " - " + title.replace("/", "-").replace(".", "") + ".pdf"
                logger.debug ("    {0} == {1} == {2} == {3}".format(code, title, href, filename))

                if old_code == "" or old_code == code:
                    tmpPages[title] = href, filename
                    old_code = code
                    old_name = name
                elif old_code != code:
                    # add the links to the page structure
                    updateAipPageLinks (type, old_code, dromeMapping[old_code], tmpPages)

                    tmpPages = {}
                    tmpPages[title] = href, filename
                    old_code = code
                    old_name = name

                code = ""
                title = ""
                href = ""

    if (type and code and title and href and filename):
        filename = code + " - " + title.replace("/", "-").replace(".", "") + ".pdf"
        logger.debug ("    {0} == {1} == {2} == {3}".format(code, title, href, filename))

        if old_code == "" or old_code == code:
            tmpPages[title] = href, filename

            # add the links to the page structure
            updateAipPageLinks (type, code, dromeMapping[code], tmpPages)
        elif old_code != code:
            # add the links to the page structure
            updateAipPageLinks (type, old_code, dromeMapping[old_code], tmpPages)

            aipPages[type][old_code]["PageLinks"] = tmpPages
            tmpPages = {}
            tmpPages[title] = href, filename

            # add the links to the page structure
            updateAipPageLinks (type, code, dromeMapping[code], tmpPages)

    return


#
# parse the main FI AIP page to get list of Aerodromes and their
# associated information pages
#
def parseMainPageFI ( aipBaseUrl, aipRegion ):
    aipMainPage = "{0}/eaip/en/index3.htm".format(aipBaseUrl)

    # get site page
    html = getWebPage ( "Aip",  aipRegion, aipMainPage )

    # loop through all the link tags
    type = adType2
    charts = False
    for div in html.find_all("div"):
        if div.get_text() != "AD":
            continue

        for link in html.find_all("a"):
            #logger.debug (link)
            href = ""
            code = ""
            name = ""

            if ("class" not in link.attrs):
                continue
            linkText = link.get_text().strip()
            if link["class"][0] == "level1":
                if "AD 2 Lentopaikat" == linkText:
                    charts = True
                else:
                    charts = False
            if not charts or linkText[:4] == "AD 2":
                continue

            if ("href" in link.attrs):
                href = link["href"]
                if href[-4:] != ".htm":
                    continue
            name = linkText[7:]
            code = linkText[:4]

            #logger.debug (code + "==" + href + "==" + type)

            # check if this is a valid link we want
            if (href and code):
                new_href = aipBaseUrl + "/eaip/" + href.replace("../", "")
                addAipPage (type, code, name, new_href)
                parseDromePageFI (type, code, name, aipBaseUrl, new_href)

    return


#
# parse the main FR AIP page to get list of Aerodromes and their
# associated information pages
#
def parseMainPageFR ( aipBaseUrl, aipRegion ):
    aipMainPage = "{0}/html/eAIP/FR-menu-fr-FR.html".format(aipBaseUrl)

    # get site page
    html = getWebPage ( "Aip",  aipRegion, aipMainPage )

    # loop through all the link tags
    type = ""
    for link in html.find_all("a"):
        title = ""
        href = ""
        id = ""
        code = ""
        name = " ".join(link.get_text().split())[5:]
        if ("href" in link.attrs):
            href = link["href"]
        if ("id" in link.attrs):
            id = link["id"]
            if ("AD-2plus" == id):
                type = adType2
            elif ("AD-3plus" == id):
                type = adType3
            else:
                idSplit = id.split(".")
                if len(idSplit) == 3:
                    code = idSplit[2]

        # loop through all the span tags in the link tag
        for span in link.find_all("span"):
            if ("class" not in span.attrs):
                continue
            if ( "Number" in span["class"] ):
                title = span.get_text().strip()

        #logger.debug (title + "==" + code + "==" + href + "==" + type)

        # check if this is a valid link we want
        if (not title and href != "#" and code):
            new_href = aipBaseUrl + "/html/eAIP/" + href.replace("#" + id, "")
            addAipPage (type, code, name, new_href)
            parseDromePageFR (type, code, name, aipBaseUrl, new_href)

    return


#
# parse the main IE AIP page to get list of Aerodromes and their
# associated information pages
#
def parseMainPageIE ( aipBaseUrl, aipRegion ):
    aipMainPage = "{0}/aip_directory.htm".format(aipBaseUrl)

    # get site page
    html = getWebPage ( "Aip",  aipRegion, aipMainPage )

    # loop through all the table tags
    for tr in html.find_all("tr"):
        href = ""
        code = ""
        name = ""
        type = ""
        for td in tr.find_all("td"):
            for link in tr.find_all("a"):
                if "Chart Information" in link.get_text():
                    href = link["href"]
                    code = href.split("_")[1].upper()
                    # fudge for ireland west link
                    if len(link.get_text()) > 19:
                        name = link.get_text()[:(len(link.get_text()) - 18)]
                    type = adType2
                else:
                    # fudge for ireland west link
                    name = link.get_text().strip()

        #logger.debug (name + "==" + code + "==" + href + "==" + type)

        # check if this is a valid link we want
        if (href and code):
            new_href = aipBaseUrl + "/" + href
            addAipPage (type, code, name, new_href)
            parseDromePageIE (type, code, name, aipBaseUrl, new_href)

    return


#
# parse the main NL AIP page to get list of Aerodromes and their
# associated information pages
#
def parseMainPageNL ( aipBaseUrl, aipRegion ):
    aipMainPage = "{0}/html/eAIP/EH-menu-en-GB.html".format(aipBaseUrl)

    # get site page
    html = getWebPage ( "Aip",  aipRegion, aipMainPage )

    # loop through all the link tags
    type = ""
    for link in html.find_all("a"):
        #logger.debug (link)
        title = ""
        href = ""
        id = ""
        code = link.get_text().strip()[:4]
        name = link.get_text().strip()[7:]
        if ("href" in link.attrs):
            href = link["href"]
        if ("id" in link.attrs):
            id = link["id"]
            if ("AD-2plus" == id):
                type = adType2
            elif ("AD-3plus" == id):
                type = adType3

        # loop through all the span tags in the link tag
        for span in link.find_all("span"):
            if ("class" not in span.attrs):
                continue
            if ( "Numbering" in span["class"] ):
                title = span.get_text()

        #logger.debug (title + "==" + code + "==" + name  + "==" + href + "==" + type)

        # check if this is a valid link we want
        if (not title and href != "#" and code and type):
            new_href = aipBaseUrl + "/html/" + href.replace("../", "").replace("#" + id, "")
            addAipPage (type, code, name, new_href)
            parseDromePageNL (type, code, name, aipBaseUrl, new_href)

    return


#
# parse the main NO AIP page to get list of Aerodromes and their
# associated information pages
#
def parseMainPageNO ( aipBaseUrl, aipRegion ):
    aipMainPage = "{0}/html/eAIP/EN-menu-en-GB.html".format(aipBaseUrl)

    # get site page
    html = getWebPage ( "Aip",  aipRegion, aipMainPage )

    # loop through all the link tags
    type = ""
    for link in html.find_all("a"):
        #logger.debug (link)
        title = ""
        href = ""
        id = ""
        name = link.get_text()
        if ("title" in link.attrs):
            title = link["title"].replace("\r", "").replace("\n", "")
        if ("href" in link.attrs):
            href = link["href"]
        if ("id" in link.attrs):
            id = link["id"]
            if ("AD-2plus" == id):
                type = adType2
            elif ("AD-3plus" == id):
                type = adType3

        # loop through all the span tags in the link tag
        for span in link.find_all("span"):
            if ("class" not in span.attrs):
                continue
            elif "sdParams" in span["class"]:
                sd = span.get_text()
                name = name.replace(sd, "")

        #logger.debug (title + "==" + href + "==" + name + "==" + type)

        # check if this is a valid link we want
        if (not title and href and name and type and name != "+"):
            code = name.split()[0]
            new_name = name.replace(code, "").strip()
            new_href = aipBaseUrl + "/html/" + href.replace("../", "").replace("#" + id, "")
            addAipPage (type, code, new_name, new_href)
            parseDromePageNO (type, code, new_name, aipBaseUrl, new_href)

    return


#
# parse the main RU AIP page to get list of Aerodromes and their
# associated information pages
#
def parseMainPageRU ( aipBaseUrl, aipRegion ):
    global aipPages

    aipMainPage = "{0}/html/menueng.htm".format(aipBaseUrl)

    # get site page
    html = getWebPage ( "Aip",  aipRegion, aipMainPage )

    # loop through all the link tags
    for script in html.find_all("script"):
        if ("language" in script.attrs):
            continue

        itemBegin = ""
        itemLink = ""
        type = ""
        code = ""
        name = ""
        href = ""
        title = ""
        tmpPages = {}
        for line in script.string.split("\n"):
            line = line[:-1]

            #logger.debug ( line )
            if ("ItemBegin" == line[:9]):
                itemBegin = line[10:-2].replace("\", ", ",").replace("\"", "").split(",")
                itemLink = ""
                if type in (None, ""):
                    if itemBegin[2] == "AD 2. Aerodromes":
                        logger.debug ("Found AERODROME section.")
                        type = adType2
                        continue
                    else:
                        itemBegin = ""
                        continue
                if itemBegin[2] == "AD 3 Helidromes":
                    logger.debug ("Found HELIPORT section.")
                    type = adType3
                    continue
                elif itemBegin[2] in ("AD 4 Other aerodromes", "AD 4. Other aerodromes", "Aerodromes classes 4D"):
                    logger.debug ("Found OTHER section.")
                    # not interested in anything not AD 2 or AD 3, so lets stop parsing
                    itemBegin = ""
                    type = ""
                    continue
                # only interested if its names properly
                if len(itemBegin[2]) > 4:
                    if itemBegin[2][4] == ".":
                        code = itemBegin[2][:4]
                        name = itemBegin[2][5:].strip()

                # check if this is a valid link we want
                if (code and type and name):
                    # set flag to ignore duplicates, as site repeats drome data multiple times
                    addAipPage(type, code, name, "", True)
            if ("ItemLink" == line[:8]):
                if (not itemBegin):
                    continue
                itemLink = line[9:-2].replace("\", ", ",").replace("\"", "").split(",")
                href = itemLink[0]
                title = "".join(itemLink[1:])
                if "(" in title:
                    title = "".join(title.split(") ")[1:])
                # check we have both parts
                if (code and title and href):
                    new_href = aipBaseUrl + "/" + href.replace("../", "")
                    filename = code + " - " + title.replace(".", "") + ".pdf"
                    tmpPages[title] = new_href, filename
                    logger.debug ("    {0} == {1} == {2} == {3}".format(code, title, new_href, filename))

            if ("ItemEnd" == line[:7]):
                if (not itemBegin):
                    continue

                # add the links to the page structure
                updateAipPageLinks (type, code, name, tmpPages)

                itemBegin = ""
                itemLink = ""
                tmpPages = {}

    return


#
# parse the main SE AIP page to get list of Aerodromes and their
# associated information pages
#
def parseMainPageSE ( aipBaseUrl, aipRegion ):
    aipMainPage = "{0}/Editorial/View/IAIP?folderId=19".format(aipBaseUrl)

    # get site page
    html = getWebPage ( "AIP",  aipRegion, aipMainPage )

    # loop through all the link tags
    type = adType2
    for table in html.find_all("table"):
        #logger.debug (table)
        href = ""
        code = ""
        name = ""
        for tr in table.find_all("tr"):
            for td in tr.find_all("td"):
                for link in td.find_all("a"):
                    if ("class" in link.attrs):
                        if "sortableFolder--rightArrow" in link["class"]:
                            name = link.get_text()
                    else:
                        code = link.get_text()
                        href = link["href"]

            #logger.debug (code + "==" + href + "==" + name)

            # check if this is a valid link we want
            if (href and code):
                new_href = aipBaseUrl + "/" + href
                addAipPage (type, code, name, new_href)
                parseDromePageSE (type, code, name, aipBaseUrl, new_href)

    return


#
# parse the main UK AIP page to get list of Aerodromes and their
# associated information pages
#
def parseMainPageUK ( aipBaseUrl, aipRegion ):
    aipMainPage = "{0}/html/eAIP/EG-menu-en-GB.html".format(aipBaseUrl)

    # get site page
    html = getWebPage ( "AIP",  aipRegion, aipMainPage )

    # loop through all the link tags
    type = ""
    for link in html.find_all("a"):
        title = ""
        href = ""
        id = ""
        code = ""
        name = ""

        code = link.get_text().split()[0]

        if ("title" in link.attrs):
            title = link["title"].replace("\r", "").replace("\n", "")
        if ("href" in link.attrs):
            href = link["href"]
        if ("id" in link.attrs):
            id = link["id"]
            if ("AD-2plus" == id):
                type = adType2
            elif ("AD-3plus" == id):
                type = adType3

        # loop through all the span tags in the link tag
        for span in link.find_all("span"):
            if ("class" not in span.attrs):
                continue
            if ( "SD" in span["class"] ):
                name = span.get_text()

#        logger.debug (title + "==" + code + "==" + href + "==" + type)

        # check if this is a valid link we want
        if (not title and href != "#" and code and type):
            new_href = aipBaseUrl + "/html/" + href.replace("../", "").replace("#" + id, "")
            addAipPage (type, code, name, new_href)
            parseDromePageUK (type, code, name, aipBaseUrl, new_href)

    return


#
# parse the BE AIP airodrome page to get list of PDF chart files that
# are available for that airodrome
#
def parseDromePageBE ( type, code, dromeTitle, baseUrl, dromeUrl ):
    # get site drome page
    html = getWebPage ( "Drome",  code, dromeUrl )

    pdfPages = {}
    newTitle = ""
    title = ""
    for tr in html.find_all("tr"):
        #logger.debug (tr)
        href = ""
        for td in tr.find_all("td"):
            title = newTitle.replace("&", "and")
            newTitle = td.get_text().strip()

            for div in td.find_all("div"):
                # check we are in the chart section
                if not div.find_all("img"):
                    continue

                # grab the link href
                for link in div.find_all("a"):
                    if ("href" in link.attrs):
                        href = link["href"]
                
        # check we have both parts
        if (title and href):
            new_href = baseUrl + "/" + href.replace("../", "")
            filename = code + " - " + title.replace("/", "-") + ".pdf"
            pdfPages[title] = new_href, filename
            logger.debug ("    {0} == {1} == {2} == {3}".format(code, title, new_href, filename))

    # add the links to the page structure
    updateAipPageLinks (type, code, dromeTitle, pdfPages)

    return


#
# parse the FI AIP airodrome page to get list of PDF chart files that
# are available for that airodrome
#
def parseDromePageFI ( type, code, dromeTitle, baseUrl, dromeUrl ):
    # get site drome page
    html = getWebPage ( "Drome",  code, dromeUrl )

    pdfPages = {}
    for td in html.find_all("td"):
        # check if we are in the charts section
        if ("class" in td.attrs):
            clas = td["class"][0]
            if (clas != "chartPad"):
                continue
        else:
            continue

        # in charts section so parse the table
        title = ""
        href = ""
        for link in td.find_all("a"):
            title = link.get_text()
            href = link["href"]

        # check we have both parts
        if (title and href):
            new_href = baseUrl + "/eaip/ad/" + code.lower() + "/" + href
            filename = code + " - " + title.replace("/", "-") + ".pdf"
            pdfPages[title] = new_href, filename
            logger.debug ("    {0} == {1} == {2} == {3}".format(code, title, new_href, filename))

    # add the links to the page structure
    updateAipPageLinks (type, code, dromeTitle, pdfPages)

    return


#
# parse the FR AIP airodrome page to get list of PDF chart files that
# are available for that airodrome
#
def parseDromePageFR ( type, code, dromeTitle, baseUrl, dromeUrl ):
    # get site drome page
    html = getWebPage ( "Drome",  code, dromeUrl )

    pdfPages = {}
    for div in html.find_all("div"):
        # check if we are in the charts section
        if ("class" in div.attrs):
            clas = div["class"][0]
            if (clas != "graphic-box"):
                continue
        else:
            continue

        # in charts section so parse the table
        title = ""
        href = ""
        for link in div.find_all("a"):
            # grab the link title and strip out the "AD 2 xxxx " bit at the start
            title = link.get_text()[10:]
            href = link["href"]

            # check we have both parts
            if (title and href):
                new_href = baseUrl + "/html/eAIP/" + href.replace(" ", "%20")
                filename = code + " - " + title + ".pdf"
                pdfPages[title] = new_href, filename
                logger.debug ("    {0} == {1} == {2} == {3}".format(code, title, new_href, filename))

    # add the links to the page structure
    updateAipPageLinks (type, code, dromeTitle, pdfPages)

    return


#
# parse the IE AIP airodrome page to get list of PDF chart files that
# are available for that airodrome
#
def parseDromePageIE ( type, code, dromeTitle, baseUrl, dromeUrl ):
    # get site drome page
    html = getWebPage ( "Drome",  code, dromeUrl )

    pdfPages = {}
    for tr in html.find_all("tr"):
        title = ""
        href = ""

        for td in tr.find_all("td"):
            # grab the link title
            for p in tr.find_all("p"):
                title = p.get_text().replace("\r", "").replace("\n", "")
            # grab the link href
            for link in tr.find_all("a"):
                if ("href" in link.attrs):
                    href = link["href"]
            
        # check we have both parts
        if (title and href):
            new_href = baseUrl + "/" + href
            filename = code + " - " + title.replace("/", "-") + ".pdf"
            pdfPages[title] = new_href, filename
            logger.debug ("    {0} == {1} == {2} == {3}".format(code, title, new_href, filename))

    # add the links to the page structure
    updateAipPageLinks (type, code, dromeTitle, pdfPages)

    return


#
# parse the NL AIP airodrome page to get list of PDF chart files that
# are available for that airodrome
#
def parseDromePageNL ( type, code, dromeTitle, baseUrl, dromeUrl ):
    # get site drome page
    html = getWebPage ( "Drome",  code, dromeUrl )

    pdfPages = {}
    for div in html.find_all("div"):
        # check if we are in the charts section
        if ("id" in div.attrs):
            id = div["id"].upper()
            if (id != code + "-AD-2.24") and (id != code + "-AD-3.23"):
                continue
        else:
            continue

        # in charts section so parse the table
        for tr in div.find_all("tr"):
            title = ""
            href = ""
            for td in tr.find_all("td"):
                if not title:
                    title = td.get_text()
                for link in tr.find_all("a"):
                    if ("href" in link.attrs):
                        href = link["href"]
            
            # check we have both parts
            if (title and href):
                new_href = baseUrl + "/" + href.replace("../", "")
                filename = code + " - " + title.replace("/", "-") + ".pdf"
                pdfPages[title] = new_href, filename
                logger.debug ("    {0} == {1} == {2} == {3}".format(code, title, new_href, filename))

    # add the links to the page structure
    updateAipPageLinks (type, code, dromeTitle, pdfPages)

    return


#
# parse the NO AIP airodrome page to get list of PDF chart files that
# are available for that airodrome
#
def parseDromePageNO ( type, code, dromeTitle, baseUrl, dromeUrl ):
    # get site drome page
    html = getWebPage ( "Drome",  code, dromeUrl )

    pdfPages = {}
    for div in html.find_all("div"):
        # check if we are in the charts section
        if ("id" in div.attrs):
            id = div["id"]
            if (id != code + "-AD-2.24") and (id != code + "-AD-3.23"):
                continue
        else:
            continue

        # in charts section so parse the table
        title = ""
        href = ""
        for tr in div.find_all("tr"):
            # grab the link title
            for p in tr.find_all("p"):
                title = p.get_text().replace("\r", "").replace("\n", "").replace("&", "and")
                href = ""
            # grab the link href
            for link in tr.find_all("a"):
                if ("href" in link.attrs):
                    href = link["href"]
            
            # check we have both parts
            if (title and href):
                new_href = baseUrl + "/" + href.replace("../", "")
                filename = code + " - " + title.replace("/", "-") + ".pdf"
                pdfPages[title] = new_href, filename
                logger.debug ("    {0} == {1} == {2} == {3}".format(code, title, new_href, filename))

    # add the links to the page structure
    updateAipPageLinks (type, code, dromeTitle, pdfPages)

    return


#
# parse the SE AIP airodrome page to get list of PDF chart files that
# are available for that airodrome
#
def parseDromePageSE ( type, code, dromeTitle, baseUrl, dromeUrl ):
    # get site drome page
    html = getWebPage ( "Drome",  code, dromeUrl )

    pdfPages = {}
    for section in html.find_all("section"):
        for li in section.find_all("li"):
            title = ""
            href = ""
            for link in li.find_all("a"):
                href = link["href"]
            for span in li.find_all("span"):
                if "document-name" == span["class"][0]:
                    title = span.get_text()

            # check we have both parts
            if (title and href):
                new_href = baseUrl + "/" + href
                filename = code + " - " + title + ".pdf"
                pdfPages[title] = new_href, filename
                logger.debug ("    {0} == {1} == {2} == {3}".format(code, title, new_href, filename))

    # add the links to the page structure
    updateAipPageLinks (type, code, dromeTitle, pdfPages)

    return


#
# parse the UK AIP airodrome page to get list of PDF chart files that
# are available for that airodrome
#
def parseDromePageUK ( type, code, dromeTitle, baseUrl, dromeUrl ):
    # get site drome page
    html = getWebPage ( "Drome",  code, dromeUrl )

    pdfPages = {}
    for div in html.find_all("div"):
        # check if we are in the charts section
        if ("id" in div.attrs):
            id = div["id"]
            if (id != code + "-AD-2.24") and (id != code + "-AD-3.23"):
                continue
        else:
            continue

        # in charts section so parse the table
        title = ""
        href = ""
        for tr in div.find_all("tr"):
            # grab the link title
            for p in tr.find_all("p"):
                title = p.get_text().replace("\r", "").replace("\n", "")
                href = ""
            # grab the link href
            for link in tr.find_all("a"):
                if ("href" in link.attrs):
                    href = link["href"]

            # check we have both parts
            if (title and href):
                new_href = baseUrl + "/" + href.replace("../", "")
                filename = code + " - " + title.replace("/", "-") + ".pdf"
                pdfPages[title] = new_href, filename
                logger.debug ("    {0} == {1} == {2} == {3}".format(code, title, new_href, filename))

    # add the links to the page structure
    updateAipPageLinks (type, code, dromeTitle, pdfPages)

    return


#
# Start of main code
#
logger.info ("Started")

#
# Parse the command line
#
parser = argparse.ArgumentParser()
parser.add_argument('--region', help='Region to generate [BE | ES | FI | FR | IE | NL | NO | RU | SE | UK]', choices=["BE", "ES", "FI", "FR", "IE", "NL", "NO", "RU", "SE", "UK"], default="UK")
parser.add_argument('--previous', action="store_true", help='User previous schedule', default=False)
parser.add_argument('--codesort', action="store_true", help='Sort by Drome code, not Drome name', default=False)
parser.add_argument('--debug', action="store_true", help='Set debug logging', default=False)
args = parser.parse_args()

aipRegion = ""
aipRegionName = ""
aipRegionUrl = ""
usePreviousSchedule = False

if args.region in aipInformation.keys():
    aipRegion = args.region
    aipRegionName = aipInformation[aipRegion][0]
    aipRegionUrl = aipInformation[aipRegion][1]
else:
    logger.fatal ("Unknown region passed: {0}".format(args.region))
    exit(1)
if args.debug:
    logging.getLogger("aipParser").setLevel(logging.DEBUG)
    console.setLevel(logging.DEBUG)
if args.codesort:
    sortOrder = "CODE"
if args.previous:
    usePreviousSchedule = True

#
# Work out what the current schedule date should be.
# Or you can just hard code it to the one you want.
#
currentDTG = datetime.datetime.now().strftime("%Y-%m-%d")
logger.debug ("Current date is [{0}]".format(currentDTG))

# loop through all the schedule dates looking for the latest
prevPublished = ""
prevRelease = ""
lastPublished = ""
lastRelease = ""
currentPublished = ""
currentRelease = ""
offsetRelease = 0
for dateLine in effectiveDates:
    publishedDate = dateLine[2]
    scheduleDate = dateLine[3]
    offsetRelease += 1
    if ( currentDTG < scheduleDate ):
        currentPublished = lastPublished
        currentRelease = lastRelease
        break
    prevPublished = lastPublished
    prevRelease = lastRelease
    lastPublished = publishedDate
    lastRelease = scheduleDate

# check if we want to use the previous schedule
if usePreviousSchedule:
    currentRelease = prevRelease
    currentPublished = prevPublished
    offsetRelease -= 1

logger.info ("Using schedule date [{0}]. Next schedule date is [{1}]".format(currentRelease, scheduleDate))

currentReleaseDTG = datetime.datetime.strptime(currentRelease, "%Y-%m-%d")
currentReleaseAlt = datetime.datetime.strftime(currentReleaseDTG, "%d_%b_%Y").upper()
currentReleaseYear = datetime.datetime.strftime(currentReleaseDTG, "%Y")
currentReleaseMonth = datetime.datetime.strftime(currentReleaseDTG, "%m")
offsetNO = 108 + offsetRelease
offsetES = 346 + offsetRelease

#
# set the base URL we want pages to hang from and then
# parse the main page and pull the airodrome page info
#
if   aipRegion == "UK":
    aipBaseUrl = "{0}/{1}-AIRAC".format(aipRegionUrl, currentRelease)
    parseMainPageUK (aipBaseUrl, aipRegion)

elif aipRegion == "BE":
    aipBaseUrl = "{0}/eaip/eAIP_Main".format(aipRegionUrl)
    parseMainPageBE (aipBaseUrl, aipRegion)

elif aipRegion == "ES":
    aipBaseUrl = "{0}/AIP".format(aipRegionUrl)
    parseMainPageES (aipBaseUrl, aipRegion)

elif aipRegion == "FI":
    aipBaseUrl = "{0}/ais".format(aipRegionUrl)
    parseMainPageFI (aipBaseUrl, aipRegion)

elif aipRegion == "FR":
    aipBaseUrl = "{0}/eAIP_{1}/FRANCE/AIRAC-{2}".format(aipRegionUrl, currentReleaseAlt, currentRelease)
    parseMainPageFR (aipBaseUrl, aipRegion)

elif aipRegion == "IE":
    aipBaseUrl = "{0}/iaip".format(aipRegionUrl)
    parseMainPageIE (aipBaseUrl, aipRegion)

elif aipRegion == "NO":
    aipBaseUrl = "{0}/AIP/View/{1}/{2}-AIRAC".format(aipRegionUrl, offsetNO, currentRelease)
    parseMainPageNO (aipBaseUrl, aipRegion)

elif aipRegion == "NL":
    aipBaseUrl = "{0}/{1}-AIRAC".format(aipRegionUrl, currentPublished)
    parseMainPageNL (aipBaseUrl, aipRegion)

elif aipRegion == "RU":
    aipBaseUrl = "{0}/common/AirInter/validaip".format(aipRegionUrl)
    parseMainPageRU (aipBaseUrl, aipRegion)

elif aipRegion == "SE":
    aipBaseUrl = "{0}".format(aipRegionUrl)
    parseMainPageSE (aipBaseUrl, aipRegion)

else:
    logger.fatal ("Unknown region passed for main page parsing: {0}".format(aipRegion))
    exit(1)


#
# create JSON output string
#

# initialise string to hold the JSON text
outputString = "{\n\t\"eBagLib\": {\n"

# add in the schedule information
if (aipRegion in ["BE", "ES", "FI", "IE", "RU", "SE"]):
    outputString += "\t\t\"0: Generated - " + currentDTG + "\": {\n"
else:
    outputString += "\t\t\"0: Published - " + currentRelease + "\": {\n"

if aipRegion == "UK":
    outputString += "\t\t\t\"10 Year Publishing Schedule\": {\n"
    outputString += "\t\t\t\t\"url\": \"https://nats-uk.ead-it.com/cms-nats/export/sites/default/en/Publications/publication-schedule/10-year-AIRAC.pdf\",\n"
    outputString += "\t\t\t\t\"filename\": \"10_Year_AIRAC.pdf\"\n"
    outputString += "\t\t\t}\n"
outputString += "\t\t},\n"


#
# loop through all the found airodromes to pull out the PDF links
# and then update the JSON output string
#
for adType in aipPages:
    if len(aipPages[adType]) == 0:
        continue

    outputString += "\t\t\"" + adType + "\": {\n"

    for key in sorted(aipPages[adType]):
        dromeStructure = aipPages[adType][key]
        dromeName = dromeStructure["Name"]
        dromeCode = dromeStructure["Code"]
        aipPdfPages = dromeStructure["PageLinks"]

        # check if we have any charts for this drome
        if len(aipPdfPages) > 0:
            if sortOrder == "NAME":
                outputString += "\t\t\t\"" + dromeName + " : " + dromeCode + "\": {\n"
            else:
                outputString += "\t\t\t\"" + dromeCode + " - " + dromeName + "\": {\n"
        
            # loop through all the PDF links to generate the schema
            for title in aipPdfPages:
                pdf_href, filename = aipPdfPages[title]
                outputString += "\t\t\t\t\"" + title + "\": {\n"
                outputString += "\t\t\t\t\t\"url\": \"" + pdf_href + "\",\n"
                outputString += "\t\t\t\t\t\"filename\": \"" + filename + "\"\n"
                outputString += "\t\t\t\t},\n"

            outputString = outputString[:-2]
            outputString += "\n\t\t\t},\n"

    outputString = outputString[:-2]
    outputString += "\n\t\t},\n"

outputString = outputString[:-2]
outputString += "\n\t}\n}\n"


#
# create the JSON file
#

# output filename
outputFilename = "AIP {0}.json".format(aipRegionName)

logger.info ("Generating output file: {0}".format(outputFilename))
try:
    file = open(outputFilename, "w", encoding = "utf8")
    file.write(outputString)
    file.close()
except Exception as e:
    logger.error (traceback.format_exc())
    exit(1)


#
# lets exit
#
logger.info ("Finished")
exit(0)
