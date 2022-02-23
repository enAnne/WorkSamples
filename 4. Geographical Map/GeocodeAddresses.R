## app.R 
library(shiny)
library(shinydashboard)
library(leaflet)
library(htmlwidgets)


customers = read.csv('C:\\Users\\EEANNNG\\My Stuff\\CASE\\Engagements\\Adhoc\\Dealer Network/Customers Geocoded.csv')

m = leaflet(customers) %>% addTiles() %>% addMarkers(
  clusterOptions = markerClusterOptions()
)

saveWidget(m, file="m.html")

