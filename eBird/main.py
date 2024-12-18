from ebird.api import get_nearby_observations
from datetime import date, datetime
from bs4 import BeautifulSoup
import requests
import pickle
import glob
import os

from log import set_logger, now

logger = set_logger()

def configuration():
    ''' Read secrets (configuration) file '''
    config = {}
    with open('config', 'r') as f:
        for line in f:
            if line[0] == '!': continue
            key, val = line.split()[0:2]
            # Save as environment variable
            config[key] = val
    return config

def monthly_observations(data, month):
    ''' How to solve the problem of: "Which month pictures to show on the web?" 
        The approach here is as follows. Start with the current month. Find if
        there are any pictures for this month. Else, look at the previous month,
        until there is at least one observation available to show on the web. '''
    
    # For each available observation, this line creates a list where:
    #     0 means that the observation does not match this month
    #     1 means this observation was taken in this month
    n = [1 if mon(v)==month else 0 for k, v in data.items()]

    if sum(n): # If there's at least one observation for this month...
        return month # ... fantastic. Return this month
    else: # else...
        month -= 1 # Inspect previous month
        if not month: # Manage transition from January to December
            month = 12 # December
        return monthly_observations(data, month) # Repeat

def mon(record):
    ''' Get month from eBIRD record '''
    return datetime.strptime(record[3], 
            '%Y-%m-%d %H:%M').month

def get_month(record):
    ''' Get month from eBIRD record '''

    return datetime.strptime(record.get('obsDt'),
            '%Y-%m-%d %H:%M').month

def create_bird_archive(archive):
    ''' Initialize a bird archive. This will contain a
        history of the records found at the different sites '''

    with open(archive, 'wb') as f:
        pickle.dump({}, f)

def add_new_record(local, species, common, 
        scientific, time, site, lon, lat):
    ''' Add new bird record '''

    i = 0

    # Append new record
    while True:
        key = 'B%08d' % i # Try and see if this record name is already taken
        if key in local: # This is to avoid overwriting existing records!
            i+=1; continue # Choose a different name for this record
        local[key] = (species, common,
                scientific, time, site, lon, lat); break

def remove_duplicated_records(local):
    ''' Clean archive by removing duplicated records '''
    
    # Duplicates are removed with this instruction
    temp = {v: k for k, v in local.items()}
    # Restore original dictionary structure
    data = {v: tuple(k) for k, v in temp.items()}

    return data

def main():
    ''' Generate map and download pictures
        of birds in Galway Bay from eBird '''

    config = configuration()
    
    # Get site names 
    names = config.get('name').split(',')
    
    # Get site coordinates
    longitudes, latitudes = config.get('lon').split(','), config.get('lat').split(',')

    # eBird URL to download pictures from
    root = 'https://ebird.org/species/'

    headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36',
            'Referer': 'https://www.google.com/',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8'
            }

    # Create output directory for images
    outdir = '/data/BIRDS/'
    if not os.path.isdir(outdir):
        os.makedirs(outdir)

    for pier, lon, lat in zip(names, longitudes, latitudes):
        # Check if a bird archive exists from a previous run
        archive = f'{outdir}{pier}.pkl'
        if os.path.isfile(archive):
            with open(archive, 'rb') as f:
                BIRDS = pickle.load(f)
        else:
            create_bird_archive(archive)
            BIRDS = {} # Empty archive

        logger.info(f'{now()} Getting latest records from eBird API for {pier}')
        records = get_nearby_observations(
                config.get('key'),               # eBird API key
                float(lat),                      # Latitude
                float(lon),                      # Longitude
                dist=float(config.get('dist')),  # Search radius [km]
                back=30)                         # Search last month

        if not records:
            logger.warning(f'{now()} No records found for {pier}')

        for i in records:
            # Get species identifier
            species = i.get('speciesCode')
            # Get common name
            common = i.get('comName')
            # Get formal (scientific) name
            scientific = i.get('sciName')
            # Get time of observation
            time = i.get('obsDt')
            # Get site
            site = i.get('locName')
            # Get longitude of observation
            lon = str(i.get('lng'))
            # Get latitude of observation
            lat = str(i.get('lat'))

            logger.debug(f'{now()}    Found {common} ({scientific}) on {time} at {site}')

            # Add new record to bird archive
            add_new_record(BIRDS, species, common, scientific, time, site, lon, lat) 

            M = get_month(i)

            # Prepare output directory to download bird pictures to
            imdir = f'{outdir}{pier}/{"%02d" % M}/'
            if not os.path.isdir(imdir):
                os.makedirs(imdir)

            # Set image file name to download
            filename = f'{imdir}{species}.jpg'
            if os.path.isfile(filename):
                continue # Picture already downloaded

            # Set URL for this species
            url = f'{root}{species}'
            # Request HTML content
            cont = requests.get(url, headers=headers).content

            soup = BeautifulSoup(cont, 'html.parser')
            # Get full list of images in HTML
            imgall = soup.find_all('img')

            for img in imgall: # Loop along images in HTML
                src = img.get('src')
                if not 'logos' in src: # Ignore logos. We just want the birds!
                    r = requests.get(src).content
                    with open(filename, 'wb+') as f:
                        f.write(r)
                        logger.info(f'{now()}   {filename} downloaded successfully')
                        break

        # Remove duplicated records in archive
        BIRDS = remove_duplicated_records(BIRDS)
        # Write archive to disk
        with open(archive, 'wb') as f:
            pickle.dump(BIRDS, f)

    month = date.today().month
    # Current month name
    monthstr = date.today().strftime('%B')

    # Post-process archive files to filter out only those
    # sightings that should be included on the website.

    files = glob.glob(f'{outdir}*.pkl')
    for file in files:
        if 'WEB' in file: continue
        # Get site name
        site = file[0:-4]; logger.info(f'{now()} Preparing web output for {site}...')

        # Dictionary with longitudes, latitude, times, 
        # scientific and common names, and pictures.
        web = {'lonBird': [], 'latBird': [], 't': [], 'sc': [], 'cm': [], 'pic': [], 'loc': []}
        
        with open(file, 'rb') as f:
            data = pickle.load(f)

        if data:
            # Month to take observations from for this site
            month_i = monthly_observations(data, month)
            # Get name of this month
            month_istr = date(2000, month_i, 1).strftime('%B')

            web['title'] = f'Birds in {month_istr}'

            for k, v in data.items():
                # Get time of observation
                time = datetime.strptime(v[3], '%Y-%m-%d %H:%M')
                if time.month == month_i: 
                    web['cm'].append(v[1])  # Append common name
                    web['sc'].append(v[2])  # Append scientific name
                    web['t'].append(v[3])   # Append time of observation
                    web['loc'].append(v[4]) # Append site of observation
                    web['lonBird'].append(v[5]) # Append longitude
                    web['latBird'].append(v[6]) # Append latitude
                    # Append path to bird picture
                    web['pic'].append(f'{site}/%02d/{v[0]}.jpg' % time.month)

        else: # No data available for this site (yet)
            web['title'] = f'No bird observations for this site (yet)'

        # Export to new file
        with open(f'{site}-WEB.pkl', 'wb') as f:
            pickle.dump(web, f)

    logger.info(f'{now()} END')

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.error(str(e))
