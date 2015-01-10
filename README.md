NZTA's Crash Analysis System (CAS)
==================================

An interactive web map of the New Zealand Transport Agency's Crash Analysis System (CAS) data, representing all accidents that have been attended by police, given a location, and that we have chosen to present (based on currency).

[**Take me to the map**](http://www.nearimprov.com/national-crash-statistics)

Made with **Python** (to read the raw CSVs and produce a nice GeoJSON with useful filters and attributes to build the popups) and **Leaflet** (to display the GeoJSON on the map).

[**An early version was featured on the NZ Herald data blog and was the most read article Christmas Day 2014**](http://www.nzherald.co.nz/nz/news/article.cfm?c_id=1&objectid=11378832)

Acknowledgements
----------------
* **Chris Hewitt** (NZTA), for early feedback and a "go ahead"
* **Tom Pettit** (Wellington City Council; New Zealand Centre for Sustainable Cities) for support and feedback
* The **NZTA**, for publishing this data in a largely machine-readable format
* **[Harkanwal Singh](http://www.nzherald.co.nz/Harkanwal-Singh/news/headlines.cfm?a_id=930)**, the New Zealand Herald Data Editor, for featuring the map.

Want to contribute?
-------------------
Please, feel absolutely free. The data is open, and so is this. Get the map working on your local computer with the following terminal commands:

```bash
cd /path/to/directory/
git clone https://github.com/alpha-beta-soup/national-crash-statistics
cd ./source/
```
If you have Python2, then run
```bash
python -m SimpleHTTPServer 8000
```
If you have Python3:
```bash
python3 -m http.server 8000
```

The navigate to [http://localhost:8000/](http://localhost:8000/) in your browser to have a look at the map. This is how you can preview any changes you make.

The basic structure is as follows:
* `nzta2geojson.py` creates the file `data.geojson` that represents the location of each crash. Its properties are what the filters look for (e.g. `alcohol = true` will give you all accidents where alcohol was a listed "role or factor" in the accident). The Python script is what performs these checks, once, before writing the output. This is executed with `cd source/ && python nzta2geojson.py`.
* `nzta-crash-analysis.js` is the Javascript script that creates the Leaflet map and uses JQuery for the filtering proceedure.
* `index.html` and `nzta-crash-analysis.css` represent the structure of the webpage and the styling of the various elements.

There is no database, just a static file. We know that's not ideal, and are looking to scale up in the future (perhaps you can help out). When we do, we'll be able to present all 14 years' of data that is available to the public, as opposed to the 7 months' worth we show now.

Other ways to help out include designing (or re-designing if you're angry) the icons that appear in the pop-ups, or giving us feedback on what does and doesn't work so well.

We'd also love to make some interactive charts of the information, because a map doesn't even reveal the most interesting patterns that undoubtedly exist in a dataset of this nature.

