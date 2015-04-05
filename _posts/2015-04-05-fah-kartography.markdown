---
layout: post
title:  "Kartography"
date:   2015-04-05
description: "visualizing @foldingathome using @kartographjs! #dataviz #FoldingAtHome"
thumbnail:
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
 	stroke: black;
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

Back in 2008, the [Folding@home](https://folding.stanford.edu/) project released a [world map](https://folding.stanford.edu/home/maps/) with donor density overlaid as variable-sized bubbles (as seen below). These sorts of visualization are appropriately named [bubble maps](http://bost.ocks.org/mike/bubble-map/), and they yield a ton of geographic information in a relatively simple layout.

<br/>

{% include image.html url="https://web.stanford.edu/group/pandegroup/images/FAH-May2008t.png" description="Painstakingly updated by hand." align="center" %}


At the time, the map was made by manually entering IP addresses in [Geostats](http://geostats.hostip.info/) and then projecting the latitudes and longitudes for each point onto a generic world map. When I learned about that, while coming up with ideas for a new blog post, I thought the process could use a bit of an overhaul.

<br/>

{% include image.html url="http://www.reactiongifs.com/wp-content/uploads/2013/09/hell-naw.gif" description="" align="center" description="When Kanye heard about how we made our map."%}


In this tutorial, I'll show you how to create a visually striking interactive bubble map using just a list of unique IP addresses. We'll be using `Python` to process the IP addresses and generate an [SVG](http://en.wikipedia.org/wiki/Scalable_Vector_Graphics) map of the world, and `Javascript` to make the bubble map and add interactivity.  


Dependencies
---

To work with IP addresses in `Python`, we'll need [`pandas`](http://pandas.pydata.org/),  [`python-geoip`](http://pythonhosted.org/python-geoip/) and [`geopy`](https://pypi.python.org/pypi/geopy/1.9.1). We'll also need `kartograph.py` to work with the SVG map.

Installing the first two packages is as easy as:

{% highlight bash %}
$ pip install python-geoip geopy
{% endhighlight %}

Installing `kartograph.py` is a little more involved, but on Mac OSX can be done as follows:

{% highlight bash %}
$ brew install postgresql
$ brew install gdal
$ pip install -r https://raw.github.com/kartograph/kartograph.py/master/requirements.txt
$ pip install https://github.com/kartograph/kartograph.py/zipball/master
{% endhighlight %}


Getting Coordinates
---

I'll assume that you happen to have a bunch of IP addresses just lying around to be processed. For this post, my data comes from the [Folding@home points](https://folding.stanford.edu/home/faq/faq-points/) database. Each day hundreds of thousands of people around the world donate their idle computer time to us, in order to perform simulations of biological molecules. At the moment, I'm running a [simulation](http://fah-web.stanford.edu/cgi-bin/fahproject.overusingIPswillbebanned?p=9411) of [p53](http://en.wikipedia.org/wiki/P53), a protein associated with 50% of all cancers; and since over 100,000 donors have worked on it (as of last week), I thought it'd be cool to see where my protein has traveled.

<br/>

{% include image.html url="/static/files/kartography/images/p53.png" description="My little peptide in all its glory." align="center" %}

First, we can start a `Python` session and import the following packages:
{% highlight python %}
> import json
> from geoip import geolite2
> from geopy.geocoders import Nominatim

{% endhighlight %}

{% highlight python %}
def getLonLAT(ip):
    return geolite2.lookup(ip).location
{% endhighlight %}

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

{% highlight python %}

{% endhighlight %}


<div class="fah-map">
    <div id="map"></div>
</div>
