---
layout: default
title: Contents
categories: [table]
---

<section  class="section-emphasis" style="margin-top: 0% !important; background-color: lightgray !important"> 
<ul>
    {% for post in site.posts %}
        {% if post.categories contains "tutorials" %}
    <li> 
        <a href="{{ post.url | prepend: site.baseurl }}"> {{ post.title }}</a><br/>{{ post.date | date: "%b %-d, %Y" }}
    </li>
        {% endif %}
    {% endfor %}
</ul>
</section>
