# Contact Tracing / Stakeholder Mapping
Business would like to identify the most influential people within a therapeutic area in a country. The datasets available are of stakeholders, their contributions in the medical field, as well as their connections to other stakeholders.

## Challenges
1. There are many types of contributions and different users may want to weight the contribution differently in order to identify the stakeholder with the highest importance in their field.
2. There are millions of stakeholders, and business would like to identify the person at the centre of influence, and also how to reach that person through existing connections.

## Solution approach for Challenge 1
A QlikSense app is developed where users have the ability to tweak the weights for each contribution, and each stakeholder's "Importance Score" is updated on the fly and they are ranked based on highest to lowest score, therefore the more important stakeholder is always at the top.

Screenshots are provided in "Network Graphing Tool.pptx"

## Solution approach for Challenge 2
A Plotly Dash app is developed where users can find the most influential stakeholders in a drop-down list, sorted from most to least influential, and display the network up to 5 degrees of separation. Users can also identify how an existing connection is linked to the interested stakeholder by selecting the existing connection in a 2nd dropdown.

Screenshots are provided in "Network Graphing Tool.pptx"

