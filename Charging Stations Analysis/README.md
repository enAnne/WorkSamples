# APAC Charging Stations Analysis
Markets EV readiness analysis for APAC Region 

This project provides a dashboard for the APAC markets to view the number of charging station POI's within each country.

The data is scraped using Python Selenium or API requests, from the online sources below:
  - ChargeMaps
  - EAnywhere (Thailand)
  - EVStation (Malaysia)  
  - HERE 
  - Naver (Korea)  
  - NewMotion  
  - NZ gov (New Zealand)  
  - Open Charge Map
  - OpenStreetMap
  - PlugShare
  - PlugSurfing

The data collected are charging station POI locations and the connectors available in each location, in the form of json files.
Then they are flattened into tables and further cleansed and standardized across all data sources to extract only the desired fields, such as provider, country codes, AC/DC connector types, latitude and longitude.

## Challenges
1. The POI's combined from the different sources could some be the same POI but varying slightly in naming or coordinates. 
2. Among the duplicates for the same POI, there could be varying information such as number of Connectors etc, and it is not clear which is the most correct source to represent the POI.

## Solution for Challenge 1
The duplicates in 2 data sources are identified using a technique of assignment optimization, where the goal is to minimize a score function in order to identify a match for each POI.
The score is a weighted sum of the Haversine distance between the location coordinates, and Lavhenstein distance in the names and addresses.
After the matching assignment is done, 2 POI's will be considered to be duplicates if the score is smaller than a certain threshold.
The POI's from all sources are matched and combined to form a single table of unique POI's, where each row represents a unique POI but the columns contain the information coming from all the duplicates across the different sources.

## Solution for Challenge 2
From the different versions of POI data for the same POI, the majority value for each field is used to represent the POI. 
They are the Name, Address, AC charging, DC charging and ChargingProvider.

## Dashboard
PowerBI dashboard needs to be opened using a PowerBI Desktop app.
The dashboards in tabs "Data Source Comparison" and "Provider Coverage" summarizes the list of POI's above, and provides an overview of the duplication across the different sources.
Screenshots are provided.
