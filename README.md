# Galway Bay QR
This project is a collaboration between Cuan Beo and the Marine Institute. The main outcome of this project is the deployment of several QR codes in different sites along the Galway Bay coastline. Users can scan the QR codes in their phones and obtain real-time information on tidal status, seawater temperature and salinity, and latest bird observations in the area. Tidal status and seawater temperature and salinity are derived from the Galway Bay model (https://doi.org/10.21203/rs.3.rs-4725384/v1) at all sites except for Gleninagh, where data is obtained from the Connemara model. Bird observations are obtained from the eBird project.

The software is structured in three backend containers (Galway-Bay, Connemara and eBird) and a frontend container (webapp). These containers have to be deployed independently and interact with each other through a shared volume. 

# Installation
First, download the code with:

`git clone https://github.com/IrishMarineInstitute/Galway-Bay-QR.git`

The code is structured in multiple Docker containers that communicate with each other through a shared volume. Create a Docker volume to communicate the containers:

`docker volume create shared-data`

The next step is to initialize each container. crontab is used to schedule tasks and ensure that the website updates on a regular basis. The containers work independently, so there is no need to initialize them in a specific order.

# The Galway-Bay container
Every five minutes, this container reads the latest Galway Bay forecasts from the Marine Institute THREDDS catalog (milas.marine.ie). For each site, the latest temperatures and salinities are obtained, and the absolute minima and maxima in a 3-day forecast are determined. Hourly sea levels from the operational model are interpolated to 1-minute frequency to determine the next times of high tide and low tide. This information is saved into the shared volume to be accessed by the webapp container.

In order to deploy this container, first look at the `config` file. Site names and coordinates are listed here. It is possible to add or remove sites by updating this list, making sure that sites and coordinates are separated by commas following the example provided. Sites should be within the Galway Bay model boundaries, which cover the whole of Galway Bay east of 9º12'43.2"W. To add site names containing special characters like whitespaces, follow the examples of New Quay and Bishop's Quarter. This is required to have the site names properly displayed on the portal. Also, some sites have been moved a little offshore, to ensure that the site does not dry out during the low tide. This is needed to ensure a smooth tidal signal and proper indication of low tide times.

Navigate to the Galway-Bay directory and execute the following:

`docker build -t galway:latest .; docker run -d -v shared-data:/data --name galway galway:latest;`

This builds and runs the container, linking to the shared volume created above where relevant data will be stored. Please notice that using `sudo` may be required in your system to run each `docker` instruction. To check whether the container is working properly, run:

`docker exec -it galway bash`

The process should run every five minutes (this can be modified in the `crontab` file before building the container). A logging file is created in a `/log` directory to show how the process is running.

# The Connemara container
The Connemara container works exactly in the same way as Galway-Bay. It is used to cover the site at Gleninagh, which falls outside the Galway Bay model coverage. Use same instructions for building and deploying the container.

`docker build -t connemara:latest .; docker run -d -v shared-data:/data --name connemara connemara:latest;`

# The eBird container
The eBird container takes advantage of the eBird project (ebird.org) and eBird API (pypi.org/project/ebird-api) to download latest bird observations in the area. To deploy this container, you need first to register into eBird and obtain and API key. This key should 
be entered into the `config` file, together with the site names and coordinates. The last line of the `config` is the searching radius [km] around each site to retrieve bird observations.

This job is set to run daily. An archive is kept for each site from the moment the process is run for the first time. This archive keeps the species names, times, locations and pictures for each observation. A separate file is produced for each site to keep only those observations to be displayed on the website at a given time. These are the observations for the current month, if any. Otherwise, observations from the month before are shown instead.

After setting the `config` file according to your needs, deploy the container as follows:

`docker build -t bird:latest .; docker run -d -v shared-data:/data --name bird bird:latest;`

The process should start at the time specified in the `crontab` file. Change this time if needed to check if the process runs properly, and rebuild. To rebuild any container, you may need to stop it first with:

`docker rm -f bird;`

Or change the container name accordingly. Once the `bird` process is finished, a set of files are created at the `/data/` folder for each site, containing pictures and observations.

# The webapp container
After moving to the `webapp` directory, you can deploy the web application by running:

`docker build -t webapp:latest .; docker run -d --restart=on-failure --name=webapp -p 80:80 -v $PWD:/app -v shared-data:/data webapp:latest`

You should be able to access the web application at `localhost:80` in your browser.
