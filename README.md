# Galway Bay QR
This project is a collaboration between Cuan Beo and the Marine Institute. The main outcome of this project is the deployment of several QR codes in different sites along the Galway Bay coastline. Users can scan the QR codes in their phones and obtain real-time information on tidal status, seawater temperature and salinity, and latest bird observations in the area. Tidal status and seawater temperature and salinity are derived from the Galway Bay model (https://doi.org/10.21203/rs.3.rs-4725384/v1) at all sites except for Gleninagh, where data is obtained from the Connemara model. Bird observations are obtained from the eBird project.

The software is structured in three backend containers (Galway-Bay, Connemara and eBird) and a frontend container (webapp). These containers have to be deployed independently and interact with each other through a shared volume. 

# Installation
These instructions have been tested on Ubuntu 18.04.6 LTS (Bionic Beaver). First, download the code with:

`git clone https://github.com/IrishMarineInstitute/Galway-Bay-QR.git`

The code is structured in multiple Docker containers that communicate with each other through a shared volume. Create a Docker volume to communicate the containers:

`docker volume create shared-data`

The next step is to initialize each container. crontab is used to schedule tasks and ensure that the website updates on a regular basis. The containers work independently, so there is no need to initialize them in a specific order.

# The Galway-Bay container
Every five minutes, this container reads the latest Galway Bay forecasts from the Marine Institute THREDDS catalog (milas.marine.ie). For each site, the latest temperatures and salinities are obtained, and the absolute minima and maxima in a 3-day forecast are determined. Hourly sea levels from the operational model are interpolated to 1-minute frequency to determine the next times of high tide and low tide. This information is saved into the shared volume to be accessed by the webapp container.

In order to deploy this container, first look at the `config` file. Site names and coordinates are listed here. It is possible to add or remove sites by updating this list, making sure that sites and coordinates are separated by commas following the example provided. Sites should be within the Galway Bay model boundaries, which cover the whole of Galway Bay east of 9º12'43.2"W. To add site names containing special characters like whitespaces, follow the examples of New Quay and Bishop's Quarter. This is required to have the site names properly displayed on the portal.

Navigate to the Galway-Bay directory and execute the following:

`docker build -t galway:latest .; docker run -d -v shared-data:/data --name galway galway:latest;`

This builds and runs the container, linking to the shared volume created above where relevant data will be stored. Please notice that using `sudo` may be required in your system to run each `docker` instruction. To check whether the container is working properly, run:

`docker exec -it galway bash`

The process should run every five minutes (this can be modified in the `crontab` file before building the container). A logging file is created in a `/log` directory to show how the process is running.

# The Connemara container
The Connemara container works exactly in the same way as Galway-Bay. It is used to cover the site at Gleninagh, which falls outside the Galway Bay model coverage. Use same instructions for building and deploying the container.





