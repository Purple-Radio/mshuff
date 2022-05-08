## Playlist Config

Show content is defined through the "genre" field which should contain the following fields in valid json:

| Field    | Datatype | Use Case                                                     |
| -------- | -------- | ------------------------------------------------------------ |
| sweeps   | array    | Array of strings defining what sweeper tags should be included |
| tracks   | array    | Array of tracks defining what track tags should be included  |
| bulletin | boolean  | True/False should the show lead with a bulletin              |

 This is an example of a valid playlist content definition:

```json
{"sweeps":["general"], "tracks":["daytime","morning"], bulletin:true}
```

What this means in practise is "Populate this show with tracks tagged general, sweepers tagged general, and include a bulletin if possible". 

Track/Sweeper tags are defined through the "mood" field of a library item, and multiple tags can be defined separated by whitespace. For example, a track with the mood field "daytime morning" will be valid for inclusion in playlists with "daytime" or "morning" in the tracks field.

Bulletins are constructed by finding the first library item with the title "Bulletin Intro", and then following that by the most recently uploaded track with type "BULLETIN". If no bulletin was uploaded within the last 24 hours, bulletin intros are automatically disabled to prevent outdated news being re-aired.
