# Analyze Tables
Quickly analyze tables within an SQL database, a csv file, or a dataframe through a comprehensive, visual summary statistics.

## Challenge
When there is a database of many tables and the tables contain many columns, it is hard to know what each table represents, and which fields are meaningful - unless there exists a well defined and maintained data catalogue. For exploration purpose, it is helpful to be able to quickly scan through the summary statistics of all fields within all tables in a DB. 

## Solution
This script will scan a table and create a PDF of visual summary statistics, containing only meaningful fields in the table - ie. fields that contain more than 1 type of value, and is more than 10% filled. The statistics are represented with appropriate visuals, bar charts for categorical fields, histogram for numerical fields, table counts for string fields. It also indicates the number/percentage of null records allowing users to judge if the field is sufficiently filled to be meaningful.

## Output
Sample outputs are PDF files in this folder starting with "Analyze_XXX.pdf"

