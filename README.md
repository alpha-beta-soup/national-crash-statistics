NZTA's Crash Analysis System (CAS)
==================================

An interactive web map of the New Zealand Transport Agency's Crash Analysis System (CAS) data, representing all accidents that have been attended by police, given a location, and that we have chosen to present (based on currency).

[**Take me to the map**](http://www.nearimprov.com/national-crash-statistics)

Made with **Python** (with props to pyproj, ephem, and geojson) to read the raw CSVs and produce a nice GeoJSON with useful filters and attributes to build the popups, **Leaflet** (to display the GeoJSON on the map), **Twitter Bootstrap**, **jQuery**, **yaml.js**, and the ever-awesome **moment.js**.

[**An early version was featured on the NZ Herald data blog and was the most read article Christmas Day 2014**](http://www.nzherald.co.nz/nz/news/article.cfm?c_id=1&objectid=11378832)

Acknowledgements
----------------
* **Chris Hewitt** (NZTA), for early feedback and a "go ahead"
* **Tom Pettit** (Wellington City Council; New Zealand Centre for Sustainable Cities) for support and feedback
* The **NZTA**, for publishing this data in a largely machine-readable format
* **[Harkanwal Singh](http://www.nzherald.co.nz/Harkanwal-Singh/news/headlines.cfm?a_id=930)**, the New Zealand Herald Data Editor, for featuring the map.
* **Tom Halliburton** (Hutt Cycle Network) and **James Burgess** (Cycle Aware Wellington) for their on-going assistance with convincing the NZTA of the merits of open data.

Want to contribute?
-------------------
Please, feel absolutely free. The data is open, and so is this. **NZTA users, I'd love to hear from you in particular.**

Get the map working on your local computer with the following terminal commands:

```bash
cd /path/to/directory/
git clone https://github.com/alpha-beta-soup/national-crash-statistics
cd national-crash-statistics
```
If you have Python2, then run
```bash
python -m SimpleHTTPServer 8000
```
If you have Python3:
```bash
python3 -m http.server 8000
```

Then navigate to [http://localhost:8000/](http://localhost:8000/) in your browser to have a look at the map. This is how you can preview any changes you make.

The basic structure is as follows:
* `/source/nzta2geojson.py` is a Python script to be run from the terminal, which creates the file `data.geojson` that represents the location of each crash, and contains information for constructing the popup. Its properties are what the filters look for (i.e. `alcohol is true`). The `data.geojson` can be used on the web or  in desktop GIS, and can be brought into a RDBMS with ogr2ogr (see `sql/`). There are some other utility scripts which are imported as needed.
* `nzta-crash-analysis.js` is the JavaScript that creates the Leaflet map and uses jQuery for the filtering proceedure. I have recently moved the development over to Coffeescript, so this is actually made from the file `nzta-crash-analysis.coffee`. Shout out if you need help compiling Coffeescript.
* `index.html` and `css/nzta-crash-analysis.css` represent the structure of the webpage and the styling of the various elements. Web content is in `images/`, `fonts/` and `icons/`.
* `docs/` contain documents relevant to this project, and the Crash Analysis System.
* `data/` contains the original data, as well as related data found on the Internet.
* Importantly, the `data/decoders/` directory contains a bunch of CSV and YAML files that can decode the original data found in the root of `data/`.

There is no database, just a static file. We are currently looking at web hosting options, and are looking to use GeoServer, probably on top of PostgreSQL/PostGIS (can you help?). When this is finally sorted, we'll be able to present all 15+ years' of data that is available to the public, as opposed to the handful of months' worth we show now. This may require a small amount of on-going financial support because I am not a charity and have spent way too much time on this without also emptying my wallet into it (can you help?).

Other ways to help out include designing (or re-designing if you're angry) the icons that appear in the pop-ups, or giving us feedback on what does and doesn't work so well. Feel free to make an issue or pull request for an enhancement, not just bugs or complaints. I love issues, please make lots of them, even for very small things, and things you have no idea how to do yourself.

We'd also love to make some interactive charts of the information, because a map doesn't even reveal the most interesting patterns that undoubtedly exist in a dataset of this nature.
