# aipParser  

## Introduction  
Python utility to parse / screen scrape country AIP site and pull out the PDF links in the AD2 and AD3 parts so I can generate a JSON file, for use in the eBag plugin for X-Plane  


## Python Dependencies  
Currently only tested with Python 3.8.  

Only dependency to install is the BeautifulSoup parsing library.  

To install this library you would:  
`pip install BeautifulSoup`


## Countries currently supported  
The following countries are supported in this script:  
: BE - Belgium  
: BR - Brazil  
: ES - Spain  
: FI - Finland  
: FR - France  
: IE - Ireland  
: NL - Netherlands  
: NO - Norway  
: RU - Russia  
: SE - Sweden  
: UK - United Kingdom  


## AIP schedule  
The script uses the AIP schedule details that were gotten from the UK site at:  
<https://nats-uk.ead-it.com/cms-nats/export/sites/default/en/Publications/publication-schedule/10-year-AIRAC.pdf>  


## Running the script  
To run the script you need to specify the ccountry you want to generate you would use the region tag **--region XX** where XX is the country code e.g. if you want the UK you would:  
`python aipParser.py --region UK`  

If you wanted to output more debug logging then you can use the debug tab **--debug** e.g.:  
`python aipParser.py --region UK --debug`  

The default output format for the JSON is **Aerodrome Name : Aerodrome Code**, but if you want this swapped i.e. **Aerodrome Code : Aerodrome Name** then you would use the codesort tag **--codesort** e.g.:  
`python aipParser.py --region UK --codesort`  

I have found that Norway sometimes does not publish their schedule when they should so have added the previous tag **--previous** to use the previous published schedule e.g.:  
`python aipParser.py --region NO --previous`  
