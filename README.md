# Foxhole Prediction Model

This project tracks live war events and casualty data from the game [Foxhole](https://www.foxholegame.com/) using the official WarAPI. It stores event data and casualty statistics in CSV files. Later this data will be used withy machine learning models in order to predict the outcome of wars.


## Data Last Updated - 7/4/2025


## Features

- **Casualty Logger:** Logs total casualties for both Colonial and Warden factions every 15 minutes.
- **Event Logger:** Tracks significant in-game events, such as the capture of bases, resource fields, and other strategic points.
- **Data Storage:** Saves all collected data in CSV format for easy analysis.

## How Data Collection Works

The scripts make requests to the Foxhole War API to get the current state of the war. This data is then processed and appended to CSV files in the `war_data` and `live_war_events` directories.

### `foxhole_casualty_logger.py`

This script runs in a loop, fetching and logging data every 15 minutes. It collects the following information:

- **Per-Map Data:** Casualties and enlistments for each map in the current war. This data is stored in `war_data/war_[war_number].csv`.
- **Overall Summary:** A summary of the total casualties and enlistments for all maps. This data is stored in `war_data/war_[war_number]_summary.csv`.

### `foxhole_event_logger.py`

This script continuously polls the API for dynamic map data, logging any changes in the ownership of strategic locations. The following information is collected:

- **Event Timestamps:** The time at which an event occurred.
- **Map Information:** The map on which the event occurred.
- **Icon Type and Category:** The type of location that changed hands (e.g., "Town Base," "Factory," "Oil Field").
- **Team Change:** The previous and current owners of the location.

This data is stored in `live_war_events/foxhole_events_war_[war_number].csv`.




## Upcoming Work:
This data will be used to build predictive models to forecast future outcomes of wars in Foxhole.





