#(C) Copyright EuroSea H2020 project under Grant No. 862626. All rights reserved.

# Copyright notice
#   --------------------------------------------------------------------
#   Copyright (C) 2022 Marine Institute
#       Diego Pereiro Rodriguez
#
#       diego.pereiro@marine.ie
#
#   This library is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This library is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this library.  If not, see <http://www.gnu.org/licenses/>.
#   --------------------------------------------------------------------

FROM tiangolo/uwsgi-nginx-flask:python3.8

MAINTAINER Diego Pereiro Rodriguez <Diego.Pereiro@Marine.ie>

ENV STATIC_URL /static
ENV STATIC_PATH /app/app/static

RUN apt-get update && \
    apt-get -y install gcc mono-mcs && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir /log
RUN mkdir /data
RUN mkdir /data/pkl
RUN mkdir /netcdf

# Create directory to keep the app code
RUN mkdir /usr/src/app
WORKDIR /usr/src/app

# Install required packages
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy required files 
COPY config .
COPY [ "*.py" , "/usr/src/app/" ]
