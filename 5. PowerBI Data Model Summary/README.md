# PowerBI Profiling
A tool to catalogue the data model in a PowerBI file in a tabular format, for thorough visibility.

## Challenge
- PowerBI desktop interface doesn't provide a single catalogue view of fields and formulas - the user has to click into each user defined field/measure to view the underlying formula, making it hard for a new developer to quickly explore and understand the data model.
- A PBIX file can easily be very huge in size if the fields were not carefully selected in the Power Query ETL stage, where all fields in the tables were loaded as is. In order to optimize performance, there is a need to reduce the data loading and thus the PBIX file size, therefore the user needs to know what are all the fields being utilized in chart visuals, measures, calculated fields, and relationships in order to load just the minimum set of neccessary fields.

## Solution
This script scans the PBIT file and extracts all the fields formulas into a catalogue. 
It also extracts all fields used in any chart visuals, measure formula, calculated fields, and relationships into a catalogue.

## Output files
AllFields_Catalogue.csv - List of all fields (calculated and base) and their formula definitions.
Used_AllFields.csv - List of all fields (calculated and base) that are used anywhere in the model.
Used_DataFields.csv - List of base fields that are used anywhere in the model (these will be the minimal set of fields to be selected in Power Query for file reduction)