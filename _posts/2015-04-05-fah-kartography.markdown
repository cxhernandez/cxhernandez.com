---
layout: post
title:  "Kartography"
date:   2015-04-05
description: "visualizing @foldingathome using @kartographjs! #dataviz #FoldingAtHome"
thumbnail: /static/images/thumbnails/kartography.png
categories: tutorials dataviz
custom_js:
- https://cdn.rawgit.com/kartograph/kartograph.org/master/js/kartograph.js
- https://cdn.rawgit.com/kartograph/kartograph.org/master/js/raphael.min.js
custom_css:
- https://cdn.rawgit.com/kartograph/kartograph.org/master/css/jquery.qtip.css

---
<style>
.mylayer {
	fill: #EDC9AF;
 	stroke: gray;
}
.ocean {
	fill: lightblue;
  	opacity: 0.2;
}
.fah-map label {
    text-align: center;
    font-style: italic;
}
.fah-map div {
    border: 1px solid #bbb;
    margin-bottom: 1em;
}
</style>
<script type="text/javascript">

$(function() {
    // initialize tooltips
    $.fn.qtip.defaults.style.classes = 'ui-tooltip-bootstrap';
    $.fn.qtip.defaults.style.def = false;
    $.getJSON('{{ site.baseurl }}/static/files/kartography/uusers.json', function(cities) {
        function map(cont, clustering) {
            var map = kartograph.map(cont);
            map.loadMap('{{ site.baseurl }}/static/files/kartography/world.svg', function() {
                map.addLayer('mylayer', {});
                map.addLayer('ocean', {});
                var scale = kartograph.scale.sqrt(cities.concat([{ nb_visits: 0 }]), 'nb_visits').range([2, 20]);
                map.addSymbols({
                    type: kartograph.Bubble,
                    data: cities,
                    clustering: clustering,
                    clusteringOpts: {
                        tolerance: 0.01,
                        maxRatio: 0.9
                    },
                    aggregate: function(cities) {
                        var nc = { nb_visits: 0, city_names: [] };
                        $.each(cities, function(i, c) {
                            nc.nb_visits += c.nb_visits;
                            nc.city_names = nc.city_names.concat(c.city_names ? c.city_names : [c.city_name]);
                        });
                        nc.city_name = nc.city_names[0] + ' and ' + (nc.city_names.length-1) + ' others';
                        return nc;
                    },
                    location: function(city) {
                        return [city.long, city.lat];
                    },
                    radius: function(city) {
                        return scale(city.nb_visits);
                    },
                    tooltip: function(city) {
                        msg = '<p>'+city.city_name+'</p>'+city.nb_visits+' donor';
                        if (city.nb_visits > 1) {
                          return msg + 's';
                        }
                        return msg;
                    },
                    sortBy: 'radius desc',
                    style: 'fill:#800; stroke: #fff; fill-opacity: 0.5;',
                });
            }, { padding: -75 });
        }
        map('#map', 'noverlap');
    });
});
</script>


Kartography <br/> (Mapping Folding@home)
---

Back in 2008, the [Folding@home](https://folding.stanford.edu/) project released a [world map](https://folding.stanford.edu/home/maps/) with showing where donors are found around the globe (as seen below). These sorts of visualization, where populations are represented as variable-sized bubbles, are appropriately named [bubble maps](http://bost.ocks.org/mike/bubble-map/), and they can yield a ton of geographic information in a relatively simple layout.

<br/>

{% include image.html url="https://web.stanford.edu/group/pandegroup/images/FAH-May2008t.png" description="Painstakingly updated by hand." align="center" %}


At the time, the map was made by manually entering IP addresses into [Geostats](http://geostats.hostip.info/) and then projecting the latitudes and longitudes for each point onto a generic world map. When I learned about that, while coming up with ideas for a new blog post, I thought the whole process could use a bit of an overhaul.

<br/>

{% include image.html url="http://www.reactiongifs.com/wp-content/uploads/2013/09/hell-naw.gif" description="" align="center" description="When Kanye heard about how we made our map."%}


In this tutorial, I'll go over how to create a visually striking interactive bubble map using just a list of unique IP addresses. We'll be using `Python` to process the IP addresses and generate an [SVG](http://en.wikipedia.org/wiki/Scalable_Vector_Graphics) map of the world, and `Javascript` to generate the bubble map and add interactivity.  

<br/>

Dependencies
---

To work with IP addresses in `Python`, we'll need [`pandas`](http://pandas.pydata.org/),  [`python-geoip`](http://pythonhosted.org/python-geoip/) and [`geopy`](https://pypi.python.org/pypi/geopy/1.9.1). We'll also need [`kartograph.py`](http://kartograph.org/docs/kartograph.py/) to work with the SVG map.

Installing the first two packages is as easy as:

{% highlight bash %}
$ pip install python-geoip geopy pandas
{% endhighlight %}

Installing `kartograph.py` is a little more involved, but on Mac OSX can be done as follows:

{% highlight bash %}
$ brew install postgresql
$ brew install gdal
$ pip install -r https://raw.github.com/kartograph/kartograph.py/master/requirements.txt
$ pip install https://github.com/kartograph/kartograph.py/zipball/master
{% endhighlight %}

<br/>

Processing the Data
---

I'll assume that you happen to have a bunch of IP addresses just lying around to be processed. For this post, my data comes from the [Folding@home points](https://folding.stanford.edu/home/faq/faq-points/) database. Each day hundreds of thousands of people around the world donate their idle computer time to us, in order to perform simulations of biological molecules. At the moment, I'm running a [simulation](http://fah-web.stanford.edu/cgi-bin/fahproject.overusingIPswillbebanned?p=9411) of [p53](http://en.wikipedia.org/wiki/P53), a protein associated with 50% of all cancers; and since over 100,000 donors have worked on it (as of last week), I thought it'd be cool to see where my protein has traveled.

<br/>

{% include image.html url="/static/files/kartography/images/p53.png" description="My little peptide in all its glory." align="center" %}

First, we can start a `Python` session and import the following packages:
{% highlight python %}
import json
import pandas as pd
from geoip import geolite2
from geopy.geocoders import Nominatim
{% endhighlight %}

Let's define a simple function that retrieves latitude and longitude coordinates from an IP address:

{% highlight python %}
def getCoord(ip):
    return geolite2.lookup(ip).location
{% endhighlight %}

Now we can loop over our file containing our list of IPs and convert them into coordinates:

{% highlight python %}
coords = []
with open('myips.list','rb') as file:
    for ip in file.readlines():
        coords.append(getCoord(ip.strip()))
{% endhighlight %}

To find the unique coordinates and their counts, we can use `pandas`:

{% highlight python %}
s = pd.Series(coords)
ucounts = s.value_counts()
{% endhighlight %}


Next, let's write a function that takes those unique coordinates and finds a corresponding physical address. The tricky bit here is that these addresses do not have a standard format, making it somewhat difficult to parse. In the code below, I've tried to look for any reference to 'city', 'town', 'county', or 'state' (in that order). As a last resort, I'll take the last field before the country name is referenced. I also included a catch-except statement in case the lookup fails:

{% highlight python %}
def getCity(coord):
    try:
        place = geolocator.reverse(coord, timeout=10)
        address = place.raw['address']
        if 'city' in address.keys():
            city = address['city']
        elif 'town' in address.keys():
            city = address['town']
        elif 'county' in address.keys():
            city = address['county']
        elif 'state' in address.keys():
            city = address['state']
        else:
            city = place.raw['display_name'].split(',')[-2]
    except:
        city = 'unknown'
    return city
{% endhighlight %}

With this function, we all have all the pieces needed to create a JSON-formatted database of unique coordinates with city/state names and numbers of hits from that location. We loop over the unique coordinates and build the JSON list as we go along:

{% highlight python %}
info = []
for coord, count in zip(ucounts.keys(), ucounts.get_values()):
    city = ''
    if coord:
        city = getCity(coord)
        info.append({'city_name': city,
                     'lat': coord[0],
                     'long': coord[1],
                     'nb_visits': count})

json.dump(info, open('data.json', 'wb'))
{% endhighlight %}

This might take some time to run (my dataset took about an hour), but once it finishes done you'll have created `data.json`, which contains all of the information we care about for our bubble map.

<br/>

Generating the SVG Map
---

So now that we have our data properly formatted for `kartograph`, we can get started on the more artistic portion of this post: map design. `kartograph.py` requires some map template files which can be downloaded using `wget` in the terminal, like so:

{% highlight bash %}
$ wget http://www.naturalearthdata.com/http//www.naturalearthdata.com/download/50m/cultural/ne_50m_admin_0_countries.zip
$ unzip ne_50m_admin_0_countries.zip
{% endhighlight %}

If you're like me and didn't have `wget` installed on mac, luckily `homebrew` has got your back:

{% highlight bash %}
$ brew install wget
{% endhighlight %}

In the same directory, fire up `Python` again and type the following:

{% highlight python %}
from kartograph import Kartograph
K = Kartograph()

config = {
          'layers':
            { 'land':
                {'src': 'ne_50m_admin_0_countries.shp'},
              'ocean':
                {'special': 'sea'}
            },
          'proj':
            {'id': 'mercator', 'lon0': 0, 'lat0': 0},
          'bounds':
            {'mode': 'bbox','data': [-205,-70,205,80]}
         }

K.generate(config, outfile='world.svg')
{% endhighlight %}

The key parts of the code from above are the `'layers'`, `'proj'`, and `'bounds'` sections. `'layers'` comprises the different objects included in your map; in this case, I've included the `'land'` (as per our template) and the `'ocean'`. `'proj'` contains the details of your [map projection](http://en.wikipedia.org/wiki/Map_projection). There are many kinds of map projections, each with their own pros and cons. I decided to keep it simple and chose a Mercator projection (which is what most modern maps show), but feel free to mess around with the [different options](http://kartograph.org/showcase/projections/#mercator) and see what works for you. Lastly, are the `'bounds'`, which set the region of the map that you're focusing in on. The format goes `[minLon, minLat, maxLon, maxLat]`, so you can see in my example that I've overcompensated for distortion in the longitude and cropped the latitude to make the Mercator projection of the globe look better.


The last line in the code above will generate the SVG file that contains your map and should look something like this:

{% include image.html url="/static/files/kartography/images/svg.png" description="A bleak new world." align="center" %}

<br/>

Putting it all together
---

All that needs to be done now is a little copying and pasting from the `kartograph.js` [showcase page](http://kartograph.org/showcase/). We'll be basing our bubble map on their `noverlap` symbol map. The basic idea is that the location data will be clustered into larger regions of overlapping density, yielding a much cleaner looking map. You can get a really good sense of this in their [example](http://kartograph.org/showcase/clustering/).

This code will be a mix of `HTML`, `CSS`, and `JavaScript`, so go ahead and open up a text editor and copy this into it:

{% highlight html %}
<head>
  <link rel="stylesheet" href="https://cdn.rawgit.com/kartograph/kartograph.org/master/css/jquery.qtip.css">
  <link rel="stylesheet" href="https://cdn.rawgit.com/kartograph/kartograph.org/master/css/k.css">
  <script src="https://cdn.rawgit.com/kartograph/kartograph.org/master/js/kartograph.js"></script>
  <script src="https://cdn.rawgit.com/kartograph/kartograph.org/master/js/raphael.min.js"></script>
  <script src="https://cdn.rawgit.com/kartograph/kartograph.org/master/js/jquery-1.10.2.min.js"></script>
</head>

<style>
.land {
	fill: #EDC9AF;
 	stroke: gray;
}
.ocean {
	fill: lightblue;
  	opacity: 0.2;
}
.my-map label {
    text-align: center;
    font-style: italic;
}
.my-map div {
    border: 1px solid #bbb;
    margin-bottom: 1em;
}
</style>

<script type="text/javascript">

$(function() {
    // initialize tooltips
    $.fn.qtip.defaults.style.classes = 'ui-tooltip-bootstrap';
    $.fn.qtip.defaults.style.def = false;
    $.getJSON('data.json', function(cities) {
        function map(cont, clustering) {
            var map = kartograph.map(cont);
            map.loadMap('world.svg', function() {
                map.addLayer('land', {});
                map.addLayer('ocean', {});
                var scale = kartograph.scale.sqrt(cities.concat([{ nb_visits: 0 }]), 'nb_visits').range([2, 20]);
                map.addSymbols({
                    type: kartograph.Bubble,
                    data: cities,
                    clustering: clustering,
                    clusteringOpts: {
                        tolerance: 0.01,
                        maxRatio: 0.9
                    },
                    aggregate: function(cities) {
                        var nc = { nb_visits: 0, city_names: [] };
                        $.each(cities, function(i, c) {
                            nc.nb_visits += c.nb_visits;
                            nc.city_names = nc.city_names.concat(c.city_names ? c.city_names : [c.city_name]);
                        });
                        nc.city_name = nc.city_names[0] + ' and ' + (nc.city_names.length-1) + ' others';
                        return nc;
                    },
                    location: function(city) {
                        return [city.long, city.lat];
                    },
                    radius: function(city) {
                        return scale(city.nb_visits);
                    },
                    tooltip: function(city) {
                        msg = '<p>'+city.city_name+'</p>'+city.nb_visits+' hit';
                        if (city.nb_visits > 1) {
                          return msg + 's';
                        }
                        return msg;
                    },
                    sortBy: 'radius desc',
                    style: 'fill:#800; stroke: #fff; fill-opacity: 0.5;',
                });
            }, { padding: -75 });
        }
        map('#map', 'noverlap');
    });
});

</script>

<div class="my-map">
    <div id="map"></div>
</div>

{% endhighlight %}

Feel free to modify the `<style>` section to suit your aesthetics, as well as trying out the different clustering methods (none, `kmeans`, and `noverlap`) for the bubble map. Once you're done, the code can then be saved into an `.html` file and viewed in a web browser to produce something like this:

<br/>

<div class="fah-map">
    <div id="map"></div>
</div>

This map shows the all the places where my protein has been simulated using Folding@home over the past 3 months. Some highlights include the Northwest Arctic, Mecca, and Tasmania. The map is by no means perfect (there's a town west of Melbourne named '5000'?!), but it gets the job done and is super easy to deploy for future data sets by just switching out the `data.json` file. Compared to 2008, though, I'd say the results are not too shabby.

<br/>

{% include image.html url="http://www.quickmeme.com/img/05/057e5384af77d9888417b9c20704511dd80d31bd73d97cc018363901eb3b62b0.jpg" description="Obama agrees." align="center" %}

<br/>
