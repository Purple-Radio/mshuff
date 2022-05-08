## Mshuff

Mshuff is a tool designed to replace the default playlist shuffle in the open source radio broadcast and automation platform [Libretime](https://libretime.org/). The main advantages are the introduction of a biased shuffling algorithm similar to that described by [Martin Fiedler](http://keyj.emphy.de/balanced-shuffle/) and a weighted track selection algorithm. These work in tandem to produce playlists which are less likely to feature frequently played tracks and less likely to group a number of tracks by the same artist. 

This tool was originally developed for Purple Radio and as such is limited towards our specific use case, I recommend running it as an hourly cron job at 30-45 minutes past the hour, as this should ensure that it will always reload upcoming playlists before they are loaded into the shows running order.

