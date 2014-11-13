/*!
 * jQuery Cookie Plugin v1.3
 */
(function(e,t,n){function i(e){return e}function s(e){return decodeURIComponent(e.replace(r," "))}var r=/\+/g;var o=e.cookie=function(r,u,a){if(u!==n){a=e.extend({},o.defaults,a);if(u===null){a.expires=-1}if(typeof a.expires==="number"){var f=a.expires,l=a.expires=new Date;l.setDate(l.getDate()+f)}u=o.json?JSON.stringify(u):String(u);return t.cookie=[encodeURIComponent(r),"=",o.raw?u:encodeURIComponent(u),a.expires?"; expires="+a.expires.toUTCString():"",a.path?"; path="+a.path:"",a.domain?"; domain="+a.domain:"",a.secure?"; secure":""].join("")}var c=o.raw?i:s;var h=t.cookie.split("; ");for(var p=0,d=h.length;p<d;p++){var v=h[p].split("=");if(c(v.shift())===r){var m=c(v.join("="));return o.json?JSON.parse(m):m}}return null};o.defaults={};e.removeCookie=function(t,n){if(e.cookie(t)!==null){e.cookie(t,null,n);return true}return false}})(jQuery,document);

//custom
jQuery(window).load(function ($) {
    var $select = jQuery('#themeSelect');
    var $bar = jQuery('#themeSwitcher');

    $select.change(function () {
        window.location = jQuery(this).val();
    });
    var selected = $select.find("option:selected").val();

    if(!selected){
        selected = $bar.find('.dd-selected-value').val();
    }

    if (!jQuery.cookie(selected)) {
        jQuery('body').addClass('hasCtBar');
        $bar.show();
        var barHeight = 60;
        var $s =jQuery('.navbar.navbar-fixed-top');
        var $e = jQuery('body.fixed-menu-navbar');

        if($e.length){
            var $n =jQuery('.navbar-static-top.navbar');
            $n.css('top',barHeight+'px');
            jQuery('body').css('margin-top',$n.height()+barHeight);
        }else if($s.length){
            $s.css('top',barHeight+'px');
            jQuery('body').css('margin-top',$s.height()+barHeight).css('padding-top',0);
        } else {
            jQuery('html').css('padding-top',barHeight);
        }
    }

    $bar.find('.switcherClose').click(function () {
        jQuery.cookie(selected, true); //session cookie
        document.location.reload(true);
    });
    var topHref = '';
    try {
            topHref = top.location.href;
    } catch(e){
        topHref = '';
    }

    //remove any externals iframes
    if (top.location != location && (topHref==''||topHref.indexOf('#')!=-1)) {
        top.location.href = document.location.href ;
    }

});