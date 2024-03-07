### archicad-zone-automate
A small script for Graphisoft Archicad to automate some routine operations with zones – to collect gross areas, writes back to props, etc.

`cmd_area_update`

Summarizes zone gross and live areas by specified zone tag (i.e., identificator for logical assembly, like "appartment" containing a couple of spaces: kitchen, bedrooms, corridors, etc.). Writes back to each zone into the user defined properties.<br/>
Project file shall contain the next user properties:

`tag` – string user property with expression to specify unique but dynamic identifier for each logical assembly (i.e. appartment ID);<br/>
`live` – boolean user property to define whether zone is live (i.e. bedroom);<br/>
`area_gross` – area user property to write the result gross space of each logical assembly;<br/>
`area_live` – area user property to write the result live space;<br/>
`update` – string user property to keep the date of last zone refresh made by the script;

The name of these properties may differ, so there's a config section where their names and groups could be specified individually.
Zones are filtered by the given single `layer` name in the config section.




