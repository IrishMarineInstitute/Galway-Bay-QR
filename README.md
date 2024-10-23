# Galway Bay QR
This project is a collaboration between Cuan Beo and the Marine Institute. The main outcome of this project is the deployment of several QR codes in different sites along the Galway Bay coastline. Users can scan the QR codes in their phones and obtain real-time information on tidal status, seawater temperature and salinity, and latest bird observations in the area. Tidal status and seawater temperature and salinity are derived from the Galway Bay model (https://doi.org/10.21203/rs.3.rs-4725384/v1) at all sites except for Gleninagh, where data is obtained from the Connemara model. Bird observations are obtained from the eBird project.

The software is structured in three backend containers (Galway-Bay, Connemara and eBird) and a frontend container (webapp). These containers have to be deployed independently and interact with each other through a shared volume. 

# The Galway-Bay container
Every five minutes, this container reads the latest Galway Bay forecasts from the Marine Institute THREDDS catalog (milas.marine.ie). For each site, the latest temperatures and salinities are obtained, and the absolute minima and maxima in a 3-day forecast are determined. Hourly sea levels from the operational model are interpolated to 1-minute frequency to determine the next times of high tide and low tide. This information is saved into the shared volume to be accessed by the webapp container.

In order to deploy this container, first look at the '''config''' file.
