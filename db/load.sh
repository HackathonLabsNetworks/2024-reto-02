#!/bin/bash

host=$1
port=$2
user=$3
pass=$4
ssl=$5

if [ -z $host ] && [ -z $port ] && [ -z $user ] && [ -z $pass ]
then
  mariadb="mariadb" 
elif [ -z $ssl ]
then 
  mariadb="mariadb --host ${host} --port ${port} --user ${user} -p${pass}"
else 
  mariadb="mariadb --host ${host} --port ${port} --user ${user} -p${pass} --ssl-ca ${ssl}"
fi

# Load airlines into travel.airlines
${mariadb} -e "LOAD DATA LOCAL INFILE 'data/airlines.csv' INTO TABLE airlines FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '\"' LINES TERMINATED BY '\n'" travel

echo "- airlines.csv loaded into travel.airlines"

# Load airports into travel.airlines
${mariadb} -e "LOAD DATA LOCAL INFILE 'data/airports.csv' INTO TABLE airports FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '\"' LINES TERMINATED BY '\n'" travel
echo "- airports.csv loaded into travel.airports"

## Load flights data into travel.flights
echo "- travel.flights"
  ${mariadb} -e "LOAD DATA LOCAL INFILE 'data/flights.csv' INTO TABLE flights FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '\"' LINES TERMINATED BY '\n'" travel

echo "Done!"
