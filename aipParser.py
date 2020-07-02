##################################################################
#
# Python script to parse the following locals:
#    UK - United Kingdom
#    BE - Belgium
#    FI - Finland
#    FR - France
#    IE - Ireland
#    NL - Netherlands
#    NO - Norway
#    RU - Russia
#    SE - Sweden
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
#   python aipParser.py --region UK
#   python aipParser.py --region FR --debug
#   python aipParser.py --region IE
#
##################################################################

import argparse
import datetime
import logging
import traceback
import ssl
import urllib.error
import urllib.request

from bs4 import BeautifulSoup

# AIP schedule gotten from:
#    http://www.nats-uk.ead-it.com/aip/current/misc/10_Year_AIRAC.pdf
effectiveDates = ["2019-01-03", "2019-01-31", "2019-02-28", "2019-03-28", "2019-04-25", "2019-05-23", "2019-06-20", "2019-07-18", "2019-08-15", "2019-09-12", "2019-10-10", "2019-11-07", "2019-12-05", "2020-01-02", "2020-01-30", "2020-02-27", "2020-03-26", "2020-04-23", "2020-05-21", "2020-06-18", "2020-07-16", "2020-08-13", "2020-09-10", "2020-10-08", "2020-11-05", "2020-12-03", "2020-12-31", "2021-01-28", "2021-02-25", "2021-03-25", "2021-04-22", "2021-05-20", "2021-06-17", "2021-07-15", "2021-08-12", "2021-09-09", "2021-10-07", "2021-11-04", "2021-12-02", "2021-12-30", "2022-01-27", "2022-02-24", "2022-03-24", "2022-04-21", "2022-05-19", "2022-06-16", "2022-07-14", "2022-08-11", "2022-09-08", "2022-10-06", "2022-11-03", "2022-12-01", "2022-12-29", "2023-01-26", "2023-02-23", "2023-03-23", "2023-04-20", "2023-05-18", "2023-06-15", "2023-07-13", "2023-08-10", "2023-09-07", "2023-10-05", "2023-11-02", "2023-11-30", "2023-12-28", "2024-01-25", "2024-02-22", "2024-03-21", "2024-04-18", "2024-05-16", "2024-06-13", "2024-07-11", "2024-08-08", "2024-09-05", "2024-10-03", "2024-10-31", "2024-11-28", "2024-12-26"]

# UK AIP website
aipRootUrlUK = "https://www.aurora.nats.co.uk/htmlAIP/Publications"

# BE AIP website
aipRootUrlBE = "https://ops.skeyes.be/html/belgocontrol_static"

# ES AIP website
aipRootUrlES = "https://ais.enaire.es/AIP"

# FI AIP website
aipRootUrlFI = "https://ais.fi"

# FR AIP website
aipRootUrlFR = "https://www.sia.aviation-civile.gouv.fr/dvd"

# NL AIP website
aipRootUrlNL = "https://www.lvnl.nl"

# IE AIP website
aipRootUrlIE = "http://iaip.iaa.ie"

# NO AIP website
aipRootUrlNO = "https://ais.avinor.no/en"

# RU AIP website
aipRootUrlRU = "http://www.caiga.ru"

# SE AIP website
aipRootUrlSE = "https://aro.lfv.se"

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


#
# parse the main BE AIP page to get list of Aerodromes and their
# associated information pages
#
def parseMainPageBE ( aipBaseUrl, aipRegion ):
	aipMainPage = "{0}/html/eAIP/EB-menu-en-GB.html".format(aipBaseUrl)

	logger.info ("Parsing the {0} AIP main page: {1}".format(aipRegion, aipMainPage))
	try:
		# main site has broken site certificate, so ignore ssl issues
		ssl._create_default_https_context = ssl._create_unverified_context

		# open up the main page and parse it
		page = urllib.request.urlopen(aipMainPage).read()
		html = BeautifulSoup(page, "html.parser")
	except urllib.error.HTTPError as e:
		logger.error ("HTTP Error {0}: {1}".format(e.code, e.reason))
		exit(1)
	except Exception as e:
		logger.error (traceback.format_exc())
		exit(1)

	logger.debug ("	TITLE : " + html.title.string)
	#logger.debug ("	PAGE :\n{0}".format(html))

	# loop through all the link tags
	aipPages = {}
	type = ""
	for link in html.find_all("a"):
		#logger.debug (link)
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
			if ("AD-2plus" == id):
				type = "AERODROME"
			elif ("AD-3plus" == id):
				type = "HELIPORT"
			else:
				idSplit = id.split(".")
				if len(idSplit) == 2:
					code = idSplit[1]

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
			aipPages[code] = type, name, new_href
			logger.debug ("	{0} == {1} == {2} == {3}".format(type, code, name, new_href))

	return aipPages


#
# parse the main ES AIP page to get list of Aerodromes and their
# associated information pages
#
def parseMainPageES ( aipBaseUrl, aipRegion ):
	aipMainPage = "{0}/AIP.html".format(aipBaseUrl)

	logger.info ("Parsing the {0} AIP main page: {1}".format(aipRegion, aipMainPage))
	try:
		# open up the main page and parse it
		page = urllib.request.urlopen(aipMainPage).read()
		html = BeautifulSoup(page, "html.parser")
	except urllib.error.HTTPError as e:
		logger.error ("HTTP Error {0}: {1}".format(e.code, e.reason))
		exit(1)
	except Exception as e:
		logger.error (traceback.format_exc())
		exit(1)

	#https://ais.enaire.es/AIP/AIPS/AMDT_329_2020_AIRAC_06_2020/AIP/aip/ad/ad2/LECO_A_CORUNA/LE_AD_2_LECO_en.pdf

	# files containing the AD2 and AD3 data
	#https://ais.enaire.es/AIP/AIPS/AMDT_329_2020_AIRAC_06_2020/AIP/aip/ad/ad2/ad2.csv
	#https://ais.enaire.es/AIP/AIPS/AMDT_329_2020_AIRAC_06_2020/AIP/aip/ad/ad2/ad3.csv

	logger.debug ("	TITLE : " + html.title.string)
	logger.debug ("	PAGE :\n{0}".format(html))

	logger.fatal ("	Unable to continue as dont know how to get the aerodrome page data")
	exit(1)

	# loop through all the link tags
	aipPages = {}
	type = ""
	for link in html.find_all("a"):
		#logger.debug (link)
		title = ""
		href = ""
		id = ""
		code = ""
		name = ""
		if ("title" in link.attrs):
			title = link["title"].replace("\r", "").replace("\n", "")
		if ("href" in link.attrs):
			href = link["href"]
		if ("id" in link.attrs):
			id = link["id"]
			if ("AD-2plus" == id):
				type = "AERODROME"
			elif ("AD-3plus" == id):
				type = "HELIPORT"

		# loop through all the span tags in the link tag
		for span in link.find_all("span"):
			if ("class" not in span.attrs):
				continue
			if ( "SD" in span["class"] ):
				if (code):
					name = span.get_text()
				else:
					code = span.get_text()

		#logger.debug (title + "==" + code + "==" + href + "==" + type)

		# check if this is a valid link we want
		if (not title and href != "#" and code):
			new_href = aipBaseUrl + "/html/" + href.replace("../", "").replace("#" + id, "")
			aipPages[code] = type, name, new_href
			logger.debug ("	{0} == {1} == {2} == {3}".format(type, code, name, new_href))

	return aipPages


#
# parse the main FI AIP page to get list of Aerodromes and their
# associated information pages
#
def parseMainPageFI ( aipBaseUrl, aipRegion ):
	aipMainPage = "{0}/eaip/en/index3.htm".format(aipBaseUrl)

	logger.info ("Parsing the {0} AIP main page: {1}".format(aipRegion, aipMainPage))
	try:
		# open up the main page and parse it
		page = urllib.request.urlopen(aipMainPage).read()
		html = BeautifulSoup(page, "html.parser")
	except urllib.error.HTTPError as e:
		logger.error ("HTTP Error {0}: {1}".format(e.code, e.reason))
		exit(1)
	except Exception as e:
		logger.error (traceback.format_exc())
		exit(1)

	logger.debug ("	TITLE :" + html.title.string)
	#logger.debug ("	PAGE :\n{0}".format(html))

	# loop through all the link tags
	aipPages = {}
	type = "AERODROME"
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
				aipPages[code] = type, name, new_href
				logger.debug ("	{0} == {1} == {2} == {3}".format(type, code, name, new_href))

	return aipPages


#
# parse the main FR AIP page to get list of Aerodromes and their
# associated information pages
#
def parseMainPageFR ( aipBaseUrl, aipRegion ):
	aipMainPage = "{0}/html/eAIP/FR-menu-fr-FR.html".format(aipBaseUrl)

	logger.info ("Parsing the {0} AIP main page: {1}".format(aipRegion, aipMainPage))
	try:
		# open up the main page and parse it
		page = urllib.request.urlopen(aipMainPage).read()
		html = BeautifulSoup(page, "html.parser")
	except urllib.error.HTTPError as e:
		logger.error ("HTTP Error {0}: {1}".format(e.code, e.reason))
		exit(1)
	except Exception as e:
		logger.error (traceback.format_exc())
		exit(1)

	logger.debug ("	TITLE :" + html.title.string)
	#logger.debug ("	PAGE :\n{0}".format(html))

	# loop through all the link tags
	aipPages = {}
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
				type = "AERODROME"
			elif ("AD-3plus" == id):
				type = "HELIPORT"
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
			aipPages[code] = type, name, new_href
			logger.debug ("	{0} == {1} == {2} == {3}".format(type, code, name, new_href))

	return aipPages


#
# parse the main IE AIP page to get list of Aerodromes and their
# associated information pages
#
def parseMainPageIE ( aipBaseUrl, aipRegion ):
	aipMainPage = "{0}/aip_directory.htm".format(aipBaseUrl)

	logger.info ("Parsing the {0} AIP main page: {1}".format(aipRegion, aipMainPage))
	try:
		# open up the main page and parse it
		page = urllib.request.urlopen(aipMainPage).read()
		html = BeautifulSoup(page, "html.parser")
	except urllib.error.HTTPError as e:
		logger.error ("HTTP Error {0}: {1}".format(e.code, e.reason))
		exit(1)
	except Exception as e:
		logger.error (traceback.format_exc())
		exit(1)

	logger.debug ("	TITLE :" + html.title.string)
	#logger.debug ("	PAGE :\n{0}".format(html))

	# loop through all the table tags
	aipPages = {}
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
					type = "AERODROME"
				else:
					# fudge for ireland west link
					name = link.get_text().strip()

		#logger.debug (name + "==" + code + "==" + href + "==" + type)

		# check if this is a valid link we want
		if (href and code):
			new_href = aipBaseUrl + "/" + href
			aipPages[code] = type, name, new_href
			logger.debug ("	{0} == {1} == {2} == {3}".format(type, code, name, new_href))

	return aipPages


#
# parse the main NL AIP page to get list of Aerodromes and their
# associated information pages
#
def parseMainPageNL ( aipBaseUrl, aipRegion ):
	aipMainPage = "{0}/html/eAIP/EH-menu-en-GB.html".format(aipBaseUrl)

	logger.info ("Parsing the {0} AIP main page: {1}".format(aipRegion, aipMainPage))
	try:
		# open up the main page and parse it
		page = urllib.request.urlopen(aipMainPage).read()
		html = BeautifulSoup(page, "html.parser")
	except urllib.error.HTTPError as e:
		logger.error ("HTTP Error {0}: {1}".format(e.code, e.reason))
		exit(1)
	except Exception as e:
		logger.error (traceback.format_exc())
		exit(1)

	logger.debug ("	TITLE : " + html.title.string)
	#logger.debug ("	PAGE :\n{0}".format(html))

	# loop through all the link tags
	aipPages = {}
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
				type = "AERODROME"
			elif ("AD-3plus" == id):
				type = "HELIPORT"

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
			aipPages[code] = type, name, new_href
			logger.debug ("	{0} == {1} == {2} == {3}".format(type, code, name, new_href))

	return aipPages


#
# parse the main NO AIP page to get list of Aerodromes and their
# associated information pages
#
def parseMainPageNO ( aipBaseUrl, aipRegion ):
	aipMainPage = "{0}/html/eAIP/EN-menu-en-GB.html".format(aipBaseUrl)

	logger.info ("Parsing the {0} AIP main page: {1}".format(aipRegion, aipMainPage))
	try:
		# open up the main page and parse it
		page = urllib.request.urlopen(aipMainPage).read()
		html = BeautifulSoup(page, "html.parser")
	except urllib.error.HTTPError as e:
		logger.error ("HTTP Error {0}: {1}".format(e.code, e.reason))
		exit(1)
	except Exception as e:
		logger.error (traceback.format_exc())
		exit(1)

	logger.debug ("	TITLE : " + html.title.string)
	#logger.debug ("	PAGE :\n{0}".format(html))

	# loop through all the link tags
	aipPages = {}
	type = ""
	for link in html.find_all("a"):
		#logger.debug (link)
		title = ""
		href = ""
		id = ""
		sd = ""
		code = ""
		name = link.get_text()
		if ("title" in link.attrs):
			title = link["title"].replace("\r", "").replace("\n", "")
		if ("href" in link.attrs):
			href = link["href"]
		if ("id" in link.attrs):
			id = link["id"]
			if ("AD-2plus" == id):
				type = "AERODROME"
			elif ("AD-3plus" == id):
				type = "HELIPORT"

		# loop through all the span tags in the link tag
		for span in link.find_all("span"):
			if ("class" not in span.attrs):
				continue
			if ( "SD" in span["class"] ):
				code = span.get_text()
			elif "sdParams" in span["class"]:
				sd = span.get_text()

		#logger.debug (title + "==" + code + "==" + sd + "==" + href + "==" + name + "==" + type)

		# check if this is a valid link we want
		if (not title and href and code):
			new_name = name.replace(code, "").replace(sd, "").strip()
			new_href = aipBaseUrl + "/html/" + href.replace("../", "").replace("#" + id, "")
			aipPages[code] = type, new_name, new_href
			logger.debug ("	{0} == {1} == {2} == {3}".format(type, code, new_name, new_href))

	return aipPages


#
# parse the main RU AIP page to get list of Aerodromes and their
# associated information pages
#
def parseMainPageRU ( aipBaseUrl, aipRegion ):
	aipMainPage = "{0}/html/menueng.htm".format(aipBaseUrl)

	logger.info ("Parsing the {0} AIP main page: {1}".format(aipRegion, aipMainPage))
	try:
		# open up the main page and parse it
		page = urllib.request.urlopen(aipMainPage).read()
		html = BeautifulSoup(page, "html.parser")
	except urllib.error.HTTPError as e:
		logger.error ("HTTP Error {0}: {1}".format(e.code, e.reason))
		exit(1)
	except Exception as e:
		logger.error (traceback.format_exc())
		exit(1)

	logger.debug ("	TITLE :" + html.title.string)
	#logger.debug ("	PAGE :\n{0}".format(html))

	# loop through all the link tags
	aipPages = {}
	pdfPages = {}
	type = "AERODROME"
	for script in html.find_all("script"):
		if ("language" in script.attrs):
			continue

		itemBegin = ""
		itemLink = ""
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
				if (int(itemBegin[0]) < 5127):
					itemBegin = ""
					continue
				if (itemBegin[1]):
					break
				code = itemBegin[2][:4]
				name = itemBegin[2][5:].strip()

				# check if this is a valid link we want
				if (code):
					aipPages[code] = type, name, ""
					logger.debug ("	{0} == {1} == {2}".format(type, code, name))
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
					logger.debug ("	{0} == {1} == {2} == {3}".format(code, title, new_href, filename))

			if ("ItemEnd" == line[:7]):
				if (not itemBegin):
					continue
				pdfPages[code] = tmpPages

				itemBegin = ""
				itemLink = ""
				tmpPages = {}

	return aipPages, pdfPages


#
# parse the main SE AIP page to get list of Aerodromes and their
# associated information pages
#
def parseMainPageSE ( aipBaseUrl, aipRegion ):
	aipMainPage = "{0}/Editorial/View/IAIP?folderId=19".format(aipBaseUrl)

	logger.info ("Parsing the {0} AIP main page: {1}".format(aipRegion, aipMainPage))
	try:
		# open up the main page and parse it
		page = urllib.request.urlopen(aipMainPage).read()
		html = BeautifulSoup(page, "html.parser")
	except urllib.error.HTTPError as e:
		logger.error ("HTTP Error {0}: {1}".format(e.code, e.reason))
		exit(1)
	except Exception as e:
		logger.error (traceback.format_exc())
		exit(1)

	logger.debug ("	TITLE :" + html.title.string)
	#logger.debug ("	PAGE :\n{0}".format(html))

	# loop through all the link tags
	aipPages = {}
	type = "AERODROME"
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
				aipPages[code] = type, name, new_href
				logger.debug ("	{0} == {1} == {2} == {3}".format(type, code, name, new_href))

	return aipPages


#
# parse the main UK AIP page to get list of Aerodromes and their
# associated information pages
#
def parseMainPageUK ( aipBaseUrl, aipRegion ):
	aipMainPage = "{0}/html/eAIP/EG-menu-en-GB.html".format(aipBaseUrl)

	logger.info ("Parsing the {0} AIP main page: {1}".format(aipRegion, aipMainPage))
	try:
		# open up the main page and parse it
		page = urllib.request.urlopen(aipMainPage).read()
		html = BeautifulSoup(page, "html.parser")
	except urllib.error.HTTPError as e:
		logger.error ("HTTP Error {0}: {1}".format(e.code, e.reason))
		exit(1)
	except Exception as e:
		logger.error (traceback.format_exc())
		exit(1)

	logger.debug ("	TITLE : " + html.title.string)
	#logger.debug ("	PAGE :\n{0}".format(html))

	# loop through all the link tags
	aipPages = {}
	type = ""
	for link in html.find_all("a"):
		#logger.debug (link)
		title = ""
		href = ""
		id = ""
		code = ""
		name = ""
		if ("title" in link.attrs):
			title = link["title"].replace("\r", "").replace("\n", "")
		if ("href" in link.attrs):
			href = link["href"]
		if ("id" in link.attrs):
			id = link["id"]
			if ("AD-2plus" == id):
				type = "AERODROME"
			elif ("AD-3plus" == id):
				type = "HELIPORT"

		# loop through all the span tags in the link tag
		for span in link.find_all("span"):
			if ("class" not in span.attrs):
				continue
			if ( "SD" in span["class"] ):
				if (code):
					name = span.get_text()
				else:
					code = span.get_text()

		#logger.debug (title + "==" + code + "==" + href + "==" + type)

		# check if this is a valid link we want
		if (not title and href != "#" and code):
			new_href = aipBaseUrl + "/html/" + href.replace("../", "").replace("#" + id, "")
			aipPages[code] = type, name, new_href
			logger.debug ("	{0} == {1} == {2} == {3}".format(type, code, name, new_href))

	return aipPages


#
# parse the BE AIP airodrome page to get list of PDF chart files that
# are available for that airodrome
#
def parseDromePageBE ( code, baseUrl, dromeUrl ):
	logger.info ("Parsing {0} Drome main page: {1}".format(code, dromeUrl))

	try:
		# open up the airodrome page and parse it
		page = urllib.request.urlopen(dromeUrl).read()
		html = BeautifulSoup(page, "html.parser")
	except urllib.error.HTTPError as e:
		logger.error ("HTTP Error {0}: {1}".format(e.code, e.reason))
		exit(1)
	except Exception as e:
		logger.error (traceback.format_exc())
		exit(1)

	logger.debug ("	TITLE : " + html.title.string)
	#logger.debug ("	PAGE :\n{0}".format(html))

	pdfPages = {}
	newTitle = ""
	title = ""
	for tr in html.find_all("tr"):
		#logger.debug (tr)
		href = ""
		for td in tr.find_all("td"):
			title = newTitle
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
			logger.debug ("	{0} == {1} == {2} == {3}".format(code, title, new_href, filename))

	return pdfPages


#
# parse the FI AIP airodrome page to get list of PDF chart files that
# are available for that airodrome
#
def parseDromePageFI ( code, baseUrl, dromeUrl ):
	logger.info ("Parsing {0} Drome main page: {1}".format(code, dromeUrl))

	try:
		# open up the airodrome page and parse it
		page = urllib.request.urlopen(dromeUrl).read()
		html = BeautifulSoup(page, "html.parser")
	except urllib.error.HTTPError as e:
		logger.error ("HTTP Error {0}: {1}".format(e.code, e.reason))
		exit(1)
	except Exception as e:
		logger.error (traceback.format_exc())
		exit(1)

	logger.debug ("	TITLE : " + html.title.string)
	#logger.debug ("	PAGE :\n{0}".format(html))

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
			logger.debug ("	{0} == {1} == {2} == {3}".format(code, title, new_href, filename))

	return pdfPages


#
# parse the FR AIP airodrome page to get list of PDF chart files that
# are available for that airodrome
#
def parseDromePageFR ( code, baseUrl, dromeUrl ):
	logger.info ("Parsing {0} Drome main page: {1}".format(code, dromeUrl))

	try:
		# open up the airodrome page and parse it
		page = urllib.request.urlopen(dromeUrl).read()
		html = BeautifulSoup(page, "html.parser")
	except urllib.error.HTTPError as e:
		logger.error ("HTTP Error {0}: {1}".format(e.code, e.reason))
		exit(1)
	except Exception as e:
		logger.error (traceback.format_exc())
		exit(1)

	logger.debug ("	TITLE : " + html.title.string)
	#logger.debug ("	PAGE :\n{0}".format(html))

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
				logger.debug ("	{0} == {1} == {2} == {3}".format(code, title, new_href, filename))

	return pdfPages


#
# parse the IE AIP airodrome page to get list of PDF chart files that
# are available for that airodrome
#
def parseDromePageIE ( code, baseUrl, dromeUrl ):
	logger.info ("Parsing {0} Drome main page: {1}".format(code, dromeUrl))

	try:
		# open up the airodrome page and parse it
		page = urllib.request.urlopen(dromeUrl).read()
		html = BeautifulSoup(page, "html.parser")
	except urllib.error.HTTPError as e:
		logger.error ("HTTP Error {0}: {1}".format(e.code, e.reason))
		exit(1)
	except Exception as e:
		logger.error (traceback.format_exc())
		exit(1)

	logger.debug ("	TITLE : " + html.title.string)
	#logger.debug ("	PAGE :\n{0}".format(html))

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
			logger.debug ("	{0} == {1} == {2} == {3}".format(code, title, new_href, filename))

	return pdfPages


#
# parse the NL AIP airodrome page to get list of PDF chart files that
# are available for that airodrome
#
def parseDromePageNL ( code, baseUrl, dromeUrl ):
	logger.info ("Parsing {0} Drome main page: {1}".format(code, dromeUrl))

	try:
		# open up the airodrome page and parse it
		page = urllib.request.urlopen(dromeUrl).read()
		html = BeautifulSoup(page, "html.parser")
	except urllib.error.HTTPError as e:
		logger.error ("HTTP Error {0}: {1}".format(e.code, e.reason))
		exit(1)
	except Exception as e:
		logger.error (traceback.format_exc())
		exit(1)

	logger.debug ("	TITLE : " + html.title.string)
	#logger.debug ("	PAGE :\n{0}".format(html))

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
				logger.debug ("	{0} == {1} == {2} == {3}".format(code, title, new_href, filename))

	return pdfPages


#
# parse the NO AIP airodrome page to get list of PDF chart files that
# are available for that airodrome
#
def parseDromePageNO ( code, baseUrl, dromeUrl ):
	logger.info ("Parsing {0} Drome main page: {1}".format(code, dromeUrl))

	try:
		# open up the airodrome page and parse it
		page = urllib.request.urlopen(dromeUrl).read()
		html = BeautifulSoup(page, "html.parser")
	except urllib.error.HTTPError as e:
		logger.error ("HTTP Error {0}: {1}".format(e.code, e.reason))
		exit(1)
	except Exception as e:
		logger.error (traceback.format_exc())
		exit(1)

	logger.debug ("	TITLE : " + html.title.string)
	#logger.debug ("	PAGE :\n{0}".format(html))

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
				logger.debug ("	{0} == {1} == {2} == {3}".format(code, title, new_href, filename))

	return pdfPages


#
# parse the SE AIP airodrome page to get list of PDF chart files that
# are available for that airodrome
#
def parseDromePageSE ( code, baseUrl, dromeUrl ):
	logger.info ("Parsing {0} Drome main page: {1}".format(code, dromeUrl))

	try:
		# open up the airodrome page and parse it
		page = urllib.request.urlopen(dromeUrl).read()
		html = BeautifulSoup(page, "html.parser")
	except urllib.error.HTTPError as e:
		logger.error ("HTTP Error {0}: {1}".format(e.code, e.reason))
		exit(1)
	except Exception as e:
		logger.error (traceback.format_exc())
		exit(1)

	logger.debug ("	TITLE : " + html.title.string)
	#logger.debug ("	PAGE :\n{0}".format(html))

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
				logger.debug ("	{0} == {1} == {2} == {3}".format(code, title, new_href, filename))

	return pdfPages


#
# parse the UK AIP airodrome page to get list of PDF chart files that
# are available for that airodrome
#
def parseDromePageUK ( code, baseUrl, dromeUrl ):
	logger.info ("Parsing {0} Drome main page: {1}".format(code, dromeUrl))

	try:
		# open up the airodrome page and parse it
		page = urllib.request.urlopen(dromeUrl).read()
		html = BeautifulSoup(page, "html.parser")
	except urllib.error.HTTPError as e:
		logger.error ("HTTP Error {0}: {1}".format(e.code, e.reason))
		exit(1)
	except Exception as e:
		logger.error (traceback.format_exc())
		exit(1)

	logger.debug ("	TITLE : " + html.title.string)
	#logger.debug ("	PAGE :\n{0}".format(html))

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
				logger.debug ("	{0} == {1} == {2} == {3}".format(code, title, new_href, filename))

	return pdfPages


#
# Start of main code
#
logger.info ("Started")

#
# Parse the command line
#
parser = argparse.ArgumentParser()
parser.add_argument('--region', help='Region to generate [BE | ES | FI | FR | IE | NL | NO | RU | SE | UK]', choices=["BE", "ES", "FI", "FR", "IE", "NL", "NO", "RU", "SE", "UK"], default="UK")
parser.add_argument('--debug', action="store_true", help='Set debug logging', default=False)
args = parser.parse_args()

aipRegion=""
aipRegionName=""
if args.region:
	aipRegion = args.region
	if   aipRegion == "UK":
		aipRegionName = "UK"
	elif aipRegion == "BE":
		aipRegionName = "Belgium"
	elif aipRegion == "ES":
		aipRegionName = "Spain"
	elif aipRegion == "FI":
		aipRegionName = "Finland"
	elif aipRegion == "FR":
		aipRegionName = "France"
	elif aipRegion == "IE":
		aipRegionName = "Ireland"
	elif aipRegion == "NO":
		aipRegionName = "Norway"
	elif aipRegion == "NL":
		aipRegionName = "Netherlands"
	elif aipRegion == "RU":
		aipRegionName = "Russia"
	elif aipRegion == "SE":
		aipRegionName = "Sweden"
	else:
		logger.fatal ("Unknown region passed: {0}".format(aipRegion))
		exit(1)
if args.debug:
	logging.getLogger("aipParser").setLevel(logging.DEBUG)
	console.setLevel(logging.DEBUG)


#
# Work out what the current schedule date should be.
# Or you can just hard code it to the one you want.
#
currentDTG = datetime.datetime.now().strftime("%Y-%m-%d")
logger.debug ("Current date is [{0}]".format(currentDTG))

# loop through all the schedule dates looking for the latest
lastRelease = ""
currentRelease = ""
offsetRelease = 0
for scheduleDate in effectiveDates:
	offsetRelease += 1
	if ( currentDTG < scheduleDate ):
		currentRelease = lastRelease
		break
	lastRelease = scheduleDate
#currentRelease = "2020-05-21"
#offsetRelease = 20

logger.info ("Using schedule date [{0}]. Next schedule date is [{1}]".format(currentRelease, scheduleDate))

currentReleaseDTG = datetime.datetime.strptime(currentRelease, "%Y-%m-%d")
currentReleaseAlt = datetime.datetime.strftime(currentReleaseDTG, "%d_%b_%Y").upper()
currentReleaseYear = datetime.datetime.strftime(currentReleaseDTG, "%Y")
currentReleaseMonth = datetime.datetime.strftime(currentReleaseDTG, "%m")
offsetNO = 70 + offsetRelease
offsetES = 308 + offsetRelease

#
# set the base URL we want pages to hang from
#

aipBaseUrlUK = "{0}/{1}-AIRAC".format(aipRootUrlUK, currentRelease)
aipBaseUrlBE = "{0}/eaip/eAIP_Main".format(aipRootUrlBE)
aipBaseUrlES = "{0}/AIPS/AMDT_{1}_{2}_AIRAC_{3}_{2}".format(aipRootUrlES, offsetES, currentReleaseYear, currentReleaseMonth)
aipBaseUrlFI = "{0}/ais".format(aipRootUrlFI)
aipBaseUrlFR = "{0}/eAIP_{1}/FRANCE/AIRAC-{2}".format(aipRootUrlFR, currentReleaseAlt, currentRelease)
aipBaseUrlIE = "{0}/iaip".format(aipRootUrlIE)
# NL does not follow standard link convention. They use date earlier than actual stated publish date. So hard code it for now
aipBaseUrlNL = "{0}/eaip/2020-06-04-AIRAC".format(aipRootUrlNL)
aipBaseUrlNO = "{0}/AIP/View/{1}/{2}-AIRAC".format(aipRootUrlNO, offsetNO, currentRelease)
aipBaseUrlRU = "{0}/common/AirInter/validaip".format(aipRootUrlRU)
aipBaseUrlSE = "{0}".format(aipRootUrlSE)


#
# parse the main page and pull the airodrome page info
#
if   aipRegion == "UK":
	aipPages = parseMainPageUK (aipBaseUrlUK, aipRegion)
elif aipRegion == "BE":
	aipPages = parseMainPageBE (aipBaseUrlBE, aipRegion)
elif aipRegion == "ES":
	aipPages = parseMainPageES (aipBaseUrlES, aipRegion)
elif aipRegion == "FI":
	aipPages = parseMainPageFI (aipBaseUrlFI, aipRegion)
elif aipRegion == "FR":
	aipPages = parseMainPageFR (aipBaseUrlFR, aipRegion)
elif aipRegion == "IE":
	aipPages = parseMainPageIE (aipBaseUrlIE, aipRegion)
elif aipRegion == "NL":
	aipPages = parseMainPageNL (aipBaseUrlNL, aipRegion)
elif aipRegion == "NO":
	aipPages = parseMainPageNO (aipBaseUrlNO, aipRegion)
elif aipRegion == "RU":
	aipPages, pdfPages = parseMainPageRU (aipBaseUrlRU, aipRegion)
elif aipRegion == "SE":
	aipPages = parseMainPageSE (aipBaseUrlSE, aipRegion)
else:
	logger.fatal ("Unknown region passed for main page parsing: {0}".format(aipRegion))
	exit(1)

#
# loop through all airodromes to create JSON output string
#

# initialise string to hold the JSON text
outputString = "{\n\t\"eBagLib\": {\n"

# add in the schedule information
if (aipRegion in ["FI", "IE", "RU", "SE"]):
	outputString += "\t\t\"0: Generated - " + currentDTG + "\": {\n"
else:
	outputString += "\t\t\"0: Published - " + currentRelease + "\": {\n"

if aipRegion == "UK":
	outputString += "\t\t\t\"10 Year Publishing Schedule\": {\n"
	outputString += "\t\t\t\t\"url\": \"http://www.nats-uk.ead-it.com/aip/current/misc/10_Year_AIRAC.pdf\",\n"
	outputString += "\t\t\t\t\"filename\": \"10_Year_AIRAC.pdf\"\n"
	outputString += "\t\t\t}\n"
outputString += "\t\t},\n"

for code in aipPages:
	type, name, href = aipPages[code]

	#
	# parse the drome page and pull the pdf info
	#
	if   aipRegion == "UK":
		aipPdfPages = parseDromePageUK (code, aipBaseUrlUK, href)
	elif aipRegion == "BE":
		aipPdfPages = parseDromePageBE (code, aipBaseUrlBE, href)
	elif aipRegion == "FI":
		aipPdfPages = parseDromePageFI (code, aipBaseUrlFI, href)
	elif aipRegion == "FR":
		aipPdfPages = parseDromePageFR (code, aipBaseUrlFR, href)
	elif aipRegion == "IE":
		aipPdfPages = parseDromePageIE (code, aipBaseUrlIE, href)
	elif aipRegion == "NL":
		aipPdfPages = parseDromePageNL (code, aipBaseUrlNL, href)
	elif aipRegion == "NO":
		aipPdfPages = parseDromePageNO (code, aipBaseUrlNO, href)
	elif aipRegion == "RU":
		aipPdfPages = pdfPages[code]
	elif aipRegion == "SE":
		aipPdfPages = parseDromePageSE (code, aipBaseUrlSE, href)
	else:
		logger.fatal ("Unknown region passed for drome page parsing: {0}".format(aipRegion))
		exit(1)

	# check if we have any charts for this drome
	if len(aipPdfPages) > 0:
		#outputString += "\t\t\"" + code + " - " + name + "\": {\n"
		outputString += "\t\t\"" + name + " : " + code + "\": {\n"
	
		# loop through all the PDF links to generate the schema
		for title in aipPdfPages:
			pdf_href, filename = aipPdfPages[title]
			outputString += "\t\t\t\"" + title + "\": {\n"
			outputString += "\t\t\t\t\"url\": \"" + pdf_href + "\",\n"
			outputString += "\t\t\t\t\"filename\": \"" + filename + "\"\n"
			outputString += "\t\t\t},\n"

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
