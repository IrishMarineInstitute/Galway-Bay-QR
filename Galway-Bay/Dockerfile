FROM python:3.8

MAINTAINER Diego Pereiro Rodriguez <Diego.Pereiro@Marine.ie>

RUN apt-get update && apt-get -y install cron vim

# Directory to store logging files
RUN mkdir /log

# Build data directory tree
RUN mkdir /data
RUN mkdir /data/pkl

WORKDIR /root

# Install required packages
COPY requirements.txt .
RUN pip install -r requirements.txt

# Set cron
COPY crontab /etc/cron.d/crontab
RUN chmod 0644 /etc/cron.d/crontab
RUN /usr/bin/crontab /etc/cron.d/crontab

# Copy required files 
COPY [ "*.py" , "/root/" ]
COPY config .

RUN echo $PYTHONPATH

CMD ["cron", "-f"]
