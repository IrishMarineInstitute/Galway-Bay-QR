''' 
    
(C) Copyright EuroSea H2020 project under Grant No. 862626. All rights reserved.

 Copyright notice
   --------------------------------------------------------------------
   Copyright (C) 2022 Marine Institute
       Diego Pereiro Rodriguez

       diego.pereiro@marine.ie

   This library is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This library is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this library.  If not, see <http://www.gnu.org/licenses/>.
   --------------------------------------------------------------------

        This is the main script of the GALWAY container. This application
   reads the Galway Bay model forecasts to provide sea level, temperature
   and salinity forecasts to users scanning the QR codes deployed by Cuan
   Beo around Galway Bay. 

'''

from netCDF4 import Dataset, num2date
from datetime import datetime, timedelta
from scipy import interpolate
import numpy as np
import pytz
from pickle import dump
from log import set_logger, now
import os

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


def get_UTC_time(timezone, minute=False):
    ''' Convert local time to UTC '''
    
    # Get local time zone
    local = pytz.UTC # pytz.timezone(timezone)
    # Current time (naive)
    now = datetime.now()    
    
    if minute:
        # Current time (naive) to minute precision
        naive = datetime(now.year, now.month, now.day, now.hour, now.minute)       
    else:
        # Current time (naive) only to hour precision
        naive = datetime(now.year, now.month, now.day, now.hour)       
        
    # Localize current time in local time zone
    local_dt = local.localize(naive, is_dst=None)
    # Convert to UTC
    return local_dt.astimezone(pytz.utc)


def reader():
    ''' Read Galway Bay model sea level time series at the 
        indicated site (LAT, LON) '''
        
    url = 'http://milas.marine.ie/thredds/dodsC/IMI_ROMS_HYDRO/GALWAY_BAY_NATIVE_70M_8L_1H/AGGREGATE'
    
    with Dataset(url) as nc:
        # Read longitude
        x = nc.variables['lon_rho'][:]
        # Read latitude
        y = nc.variables['lat_rho'][:]
        # Read sea level
        logger.info(f'{now()} Reading sea level...')
        zeta = nc.variables['zeta'][:] + 3.0 # add offset
        # Read mask
        logger.info(f'{now()} Reading mask...')
        mask = nc.variables['wetdry_mask_rho'][:]
        # Read time
        time = num2date(nc.variables['ocean_time'][:],
                        nc.variables['ocean_time'].units)
        # Read surface temperature
        logger.info(f'{now()} Reading surface temperature...')
        surface_temperature = nc.variables['temp'][:, -1, :, :]
        # Read surface temperature
        logger.info(f'{now()} Reading surface salinity...')
        surface_salinity = nc.variables['salt'][:, -1, :, :]
        logger.info(f'{now()} Finished reading from Galway Bay THREDDS...')
        
    # Set time as UTC
    time = [datetime(i.year, i.month, i.day, i.hour, 0, 0, 0, pytz.UTC) for i in time]
        
    return x, y, time, mask, zeta, surface_temperature, surface_salinity 

def find_nearest_indexes(x, y, lon, lat):     
    ''' Find indexes in ROMS grid nearest to LAT, LON location '''
    
    xlist, ylist = x[0, :], y[:, 0]
    # Find nearest indexes to LAT, LON
    idx, idy = np.argmin(abs(xlist - lon)), np.argmin(abs(ylist - lat))
    
    return idx, idy


def land_mask_areas(mask):
    ''' Given the wet & dry land mask, return an M x L array where:
        '0.0' are land areas, 
        '0.5' are intertidal areas, 
        '1.0' are sea areas '''
    
    T, _, _ = mask.shape
    
    sea = np.sum(mask, axis=0) == T    
    tidal = np.logical_and(np.sum(mask, axis=0) > 0, np.sum(mask, axis=0) < T)
    
    return  sea + 0.5 * tidal


def test_sea_level_series(zeta):
    ''' Check that the sea level series in unaffected by a drying out (i.e. its
        shape is that of a normal tidal signal, without flat values) '''
    
    k = 0.05 # [m]
    
    T = len(zeta)
    
    for i in range(T - 2):
        # Get three consecutive values
        z0, z1, z2 = zeta[i : i+3]
        # Compute differences
        d0, d1, d2 = abs(z1-z0), abs(z2-z1), abs(z2-z0)
        
        if (d0 < k) and (d1 < k) and (d2 < k): # Sea level series is flat!
            return False # The sea level series is not adequate
        
    return True # Good sea level series

def minute_interpolation(time, tide):
    ''' Interpolate hourly sea level time series to minute frequency '''
    
    # Convert time to UNIX time stamps (seconds since 1970-01-01)
    # This is needed because the scipy interpolating function cannot handle
    # datetime objects as the independent variable.
    timestamps = np.array([i.timestamp() for i in time])
    
    # Create cubic interpolator
    F = interpolate.CubicSpline(timestamps, tide)
    
    # List of time stamps to interpolate to (every minute)
    tq = np.arange(timestamps[0], timestamps[-1] + 60, 60)
        
    # Interpolate
    tideq = np.array([F(t) for t in tq])

    # What is the current index in this new time list? Convert back to datetime
    tq = [datetime.utcfromtimestamp(i) for i in tq]
    # Add the time zone information (UTC)
    tq = [i.replace(tzinfo=pytz.utc) for i in tq]
    
    return tq, tideq


def tidal_times(time, tide):
    ''' Find next high and low tide times and magnitudes '''

    '''
            UPDATE AFTER STORM EOWYN. This function only gives 
        proper results with a "well-behaved" sea level signal.
        When there is a storm surge, there can be many local
        minima and maxima in a short period of time.

        Update: this function now returns, in addition to the 
        tidal times, the number of minima and maxima found in 
        next hours. Normally, this would be just two: a minima
        (low tide) and a maxima (high tide). But if it is
        greater than two, then the tidal times are determined
        by "tidal_times_crude" below
    '''

    ''' EOWYN UPDATE '''
    nex = 0 # Eowyn update: counter for the number of minima and maxima

    exz, ext = [], [] # Extremes (minima or maxima) times and sea levels
    ''' END OF EOWYN UPDATE '''
    
    low, high = None, None
    
    # Get current trend: flood (+) or ebb (-)
    trend = tide[1] - tide[0]
    
    T = len(time)
    
    for i in range(T - 1):
        change = tide[i + 1] - tide[i]
        
        if change * trend < 0: # A change in the trend sign means a minimum or a maximum 
            ''' EOWYN UPDATE: count local minima and maxima found 
                in the next hours. '''
            nex += 1 # Count number of minima and maxima
            # Append sea level to the list of extreme sea levels
            exz.append(tide[i])
            # Append time as well
            ext.append(time[i])
            ''' END OF EOWYN UPDATE '''

            if trend < 0: # low tide
                low, low_time = tide[i], time[i]
            else: # high tide
                high, high_time = tide[i], time[i]
                
        if isinstance(low, float) and isinstance(high, float):
            # Impose that the time elapsed between low and high
            # tide must be at least five hours! If not, keep
            # searching for the next extreme until this is met.
            if abs(low_time - high_time).total_seconds() > 18000:
                break
        
        trend = change
        
    return low, low_time, high, high_time, nex, ext, exz

def tidal_times_crude(now, ext, exz):
    ''' EOWYN UPDATE: When the number of local minima or maxima is greater
    than two, simply determine the next high tide as the global maximum in
    the next 12 hours from the list of extreme sea levels; for the low tide
    use the global minima in the next 12 hours. It's not a perfect solution
    but seems to work for the Eowyn sea level signal and, hopefully, for 
    other storm surges in the future. '''

    DT = timedelta(hours=12, minutes=25) # M2 period. Exclude any minima 
    # or maxima occurring later than this time from now (the next low and
    # high tides must surely be before this time)

    low, high = 1e+3, -1e+3 # Initialize low and high tides to some dummy values

    for t, z in zip(ext, exz): # Loop along the minima and maxima identified by "tidal_times"
        if ( t - now ) > DT:
            break # Exclude the extremes occurring later than 12 h 25 min from now
        if z > high: # Higher value found, update the high tide magnitude and time
            high, high_time = z, t
        if z < low:  # Lower value found, update the low tide magnitude and time
            low, low_time   = z, t

    return low, low_time, high, high_time

def to_string(values, wetdry, timezone):
    ''' Convert numbers and times to strings. Convert current values to "LOW TIDE" 
    if "DRY" is the current status of the tide. This only applies for Bell Harbour '''
    
    local = pytz.timezone(timezone)
    
    GALWAY = {}
    
    for key, val in values.items():
        if ( 'wet' in key ) and ( not wetdry ):
            GALWAY[key] = 'LOW TIDE'
        else:
            if isinstance(val, np.float32) or isinstance(val, np.float64):
                GALWAY[key] = f'%.1f' % val
            elif isinstance(val, datetime):
                time = val.astimezone(local)                
                GALWAY[key] = time.strftime('%a %d %H:%M')
            else:
                GALWAY[key] = val
 
    return GALWAY

def decdeg2dms(dd):
    ''' Convert decimal degrees to DMS '''

    mnt,sec = divmod(abs(dd)*3600, 60)
    deg,mnt = divmod(mnt, 60)
    return f'''%02dº%02d%s%.1f"''' % (deg, mnt, '´', sec)

def main():

    try:
    
        logger.info(f'{now()} Starting GALWAY-BAY operations...')

        ''' Read configuration '''
        config = configuration()

        ''' Get local time as UTC '''
        UTC = get_UTC_time(config.get('timezone'), minute=True)
            
        ''' Get current time to be displayed on the website '''
        webtime=UTC.astimezone(pytz.timezone(config.get('timezone')))
        
        ''' Get local time as UTC (no minutes, hour precision)'''
        UTC0 = get_UTC_time(config.get('timezone'))

        ''' Get site name(s) ''' 
        names = config.get('name').split(',')
        
        ''' Get site coordinates '''
        longitudes, latitudes = config.get('lon').split(','), config.get('lat').split(',')

        ''' Read Galway Bay model '''
        logger.info(f'{now()} Reading from Galway Bay THREDDS...')
        x, y, time, mask, zeta, surf_tem, surf_sal = reader()

        for name, longitude, latitude in zip(names, longitudes, latitudes):
            # Get human-readable name of site
            nicename = name.replace("-", " ").replace("_", "'")

            # Convert coordinates from string to number
            lon, lat = float(longitude), float(latitude)
            # Convert to DMS 
            lonstr, latstr = decdeg2dms(lon), decdeg2dms(lat)
            
            ''' Find nearest indexes in grid '''
            # Current time index
            tindex = time.index(UTC0)    

            # Nearest spatial (LAT, LON) indexes
            idx, idy = find_nearest_indexes(x, y, lon, lat)   
            
            ''' Get time series for the LAT, LON site '''
            tide   = zeta[:, idy, idx] # sea level 
            wetdry = mask[:, idy, idx] # Wet & Dry status
            ST = surf_tem[:, idy, idx] # Surface temperature
            SS = surf_sal[:, idy, idx] # Surface salinity
            
            ''' GET CURRENT STATUS '''   
            WET_DRY   = wetdry[tindex]
            surface_temperature = ST[tindex]
            surface_salinity    = SS[tindex]
            
            ''' Get forecasts '''
            TF  = time[tindex::] # Forecast time
            STF = ST[tindex::] # Surface Temperature Forecast
            SSF = SS[tindex::] # Surface Salinity Forecast
            
            ''' Get forecast minima and maxima '''
            minSTF, maxSTF = min(STF), max(STF)
            minSSF, maxSSF = min(SSF), max(SSF)
            
            ''' Get indexes of minima and maxima '''
            minSTFi, maxSTFi = np.argmin(STF), np.argmax(STF)
            minSSFi, maxSSFi = np.argmin(SSF), np.argmax(SSF)
            
            ''' Get times of minima and maxima '''
            minSTFt, maxSTFt = TF[minSTFi], TF[maxSTFi]
            minSSFt, maxSSFt = TF[minSSFi], TF[maxSSFi]
                
            # Examine mask. Differentiate betweeen land (0.0) areas, intertidal (0.5)
            # areas and sea (1.0) areas. Why? The selected LAT, LON site may be in an
            # intertidal area, where it is not easy to identify the exact time of the
            # next low tide. The objective of the code below is to (1) indentify the
            # nearest grid node where the tidal signal behaves "adequately" (i.e., no
            # drying out); (2) extract the sea level series for that site. This time
            # series will then be used to idenfity the time of low tide. 
            areas = land_mask_areas(mask)
            
            ''' Check if site is either land (0.0), intertidal (0.5) or sea (1.0).
                If needed, get sea level series from a neighbouring location which 
                never dries out '''
            tipo = areas[idy, idx]
            if tipo == 0.0: # Point is on land. Wrong site. Change LAT, LON
                raise RuntimeError('Point is on land')
            elif tipo == 0.5: # Point is in an intertidal flat
                tideS = zeta[:, 35, 81] # Exception for Bell Harbour: user Bishop's Quarter sea level for tidal times
            elif tipo == 1.0: # Point is at sea
                tideS = tide
                
            ''' Interpolate to minute frequency. This is to determine the next high (or
            low) tide with enough precision '''
            logger.info(f'{now()} Interpolating sea level time series to minute frequency...')
            time_minfeq, tide = minute_interpolation(time, tideS)
            
            # Current time index
            tindex_minfeq = time_minfeq.index(UTC)    
            
            ''' Get current sea level '''
            SEA_LEVEL = tide[tindex_minfeq]
            
            ''' Find next high and low tide times and values '''
            logger.info(f'{now()} Finding next high and low tides...')
            low, low_time, high, high_time, nex, ext, exz = \
                tidal_times(time_minfeq[tindex_minfeq::], tide[tindex_minfeq::])

            ''' EOWYN UDATE ''' 
            if nex != 2:
                logger.info(f'{now()} Warning! There is something unusual in the series (a storm surge?)')
                # Find tidal times with alternative method for storm surges
                low, low_time, high, high_time = tidal_times_crude(UTC, ext, exz)
            ''' END OF EOWYN UPDATE '''
                
            ''' Find tidal status: flood or ebb '''
            change = tide[tindex_minfeq+1] - SEA_LEVEL
            if change > 0:
                STATUS, tide1extreme, tide2extreme = 'flood', 'HIGH', 'LOW'
                # Set next high tide
                tide1extremeValue, tide1extremeTime = high, high_time
                # Set next low tide
                tide2extremeValue, tide2extremeTime = low, low_time
            else:
                STATUS, tide1extreme, tide2extreme = 'ebb', 'LOW', 'HIGH'
                # Set next high tide
                tide2extremeValue, tide2extremeTime = high, high_time
                # Set next low tide
                tide1extremeValue, tide1extremeTime = low, low_time
                
            ''' Prepare output '''
            logger.info(f'{now()} Preparing output dictionary...')
            values = dict(tidewet=SEA_LEVEL, time=webtime,
                names=nicename, lon=lonstr, lat=latstr, londec=str(lon), latdec=str(lat),
                STwet=surface_temperature, 
                SSwet=round(surface_salinity), 
                minSTF=minSTF, maxSTF=maxSTF, 
                minSSF=round(minSSF), maxSSF=round(maxSSF), 
                minSTFt=minSTFt, maxSTFt=maxSTFt, 
                minSSFt=minSSFt, maxSSFt=maxSSFt, 
                tide1extreme=tide1extreme, tide2extreme=tide2extreme,
                tide1extremeValue=tide1extremeValue, tide1extremeTime=tide1extremeTime,
                tide2extremeValue=tide2extremeValue, tide2extremeTime=tide2extremeTime,
                STATUS=STATUS,  tideseries=tide, time_minfeq=time_minfeq, tindex_minfeq=tindex_minfeq, 
                          )
            logger.info(f'{now()} Converting variables to string...')
            GALWAY = to_string(values, WET_DRY, config.get('timezone'))
            
            outdir = '/data/pkl/Galway-Bay/'
            if not os.path.isdir(outdir):
                os.makedirs(outdir)

            outfile = f'{outdir}{name}.pkl'
            logger.info(f'{now()} Saving to file {outfile}...')
            with open(outfile, 'wb') as f:
                dump(GALWAY, f)

            logger.info('\n')

        logger.info(f'{now()} FINISHED...')

        return 0, ''

    except Exception as err:

        return -1, str(err)

        
if __name__ == '__main__':   
    status, err = main()
    if status:
        logger.exception(f'Exception in Galway Bay: {err}')
