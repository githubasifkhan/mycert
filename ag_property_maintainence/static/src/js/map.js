
// odoo.define('ag_property_maintainence.Maps', function (require) {

    
    var confirmBtn = document.getElementById('confirmPosition');
    var onClickPositionView = document.getElementById('onClickPositionView');
    var onIdlePositionView = document.getElementById('onIdlePositionView');
    // var latvalueView = document.getElementById('latvalueView');
    // var lngvalueView = document.getElementById('lngvalueView');
    // console.log($("input[name='geo_lat']").val())
    // this._super.apply(this, arguments);
    // var self = this;
    // console.log(self.value.geo_lat)
    // Initialize locationPicker plugin
    var lp = new locationPicker('map', {
        // lat: $("span[name='geo_lat']").text(),lng: $("span[name='geo_lon']").text(),  
        lat: 25.186233973197417,lng: 55.27260732777885,  
        // You can omit this, defaults to true
    }, {
    zoom: 15 // You can set any google map options here, zoom defaults to 15
    });
    // // function initialize(){
    //     navigator.geolocation.getCurrentPosition(function(position){
    //       // create the map here, because we only have access to position inside of this function
    //       // even if we store in a global variable, it only gets updated once this callback runs
        
    //       var currentPosition = 
    //     }
    
        
        // initialize();
    
    // Listen to button onclick event
    confirmBtn.onclick = function () {
    // Get current location and show it in HTML
    var location = lp.getMarkerPosition();
    onClickPositionView.innerHTML = 'The chosen location is ' + location.lat + ',' + location.lng;
    // latvalueView.innerHTML = 'lat :'+location.lat;
    // lngvalueView.innerHTML = 'lng :'+location.lng;
        $("input[name='geo_lat'].points").val(location.lat).focus().change();
        $("input[name='geo_lon'].pointss").val(location.lng).focus().change();
    };
    
    // Listen to map idle event, listening to idle event more accurate than listening to ondrag event
    google.maps.event.addListener(lp.map, 'idle', function (event) {
    // Get current location and show it in HTML
    var location = lp.getMarkerPosition();
    onIdlePositionView.innerHTML = 'The chosen location is ' + location.lat + ',' + location.lng;
    // latvalueView.innerHTML = location.lat;
    // lngvalueView.innerHTML = location.lng;
    });
    
// });

// odoo.define('ag_property_maintainence.mapps', function(require) {
//     'use strict';
//     var self = this;

//     var maps = require('web.core')

//     maps.extend({
//         events: {
//             'click showmap': 'showmaps',
//             'input lng': 'getlng',
//             'input lat': 'getlat',
//         },



//     });
// });
// google.maps.event.addListener(window, 'load', initialize_maps);

// Initialize map once the DOM has been loaded
// google.maps.event.addDomListener(window, 'load', initialize_map);




// odoo.define('ag_property_maintainence.maps', function(require) {
//     "use strict";
//     var core = require('web.core');
//     var QWeb = core.qweb;
//     var session = require('web.session');
    
//     div.include( {

//         // events: {
//         //     'click .oe-image-preview': 'image_preview',
//         //     'click .oe_image_list': 'image_list_view',
//         // },
//         events: {
//             'click .map': 'map_preview',
//             // 'change input': function (e) {
//             //     e.stopPropagation();
//             // }
//         },

//         map_preview : function () {
//             if (this.attrs.widget === 'maps') {
//                 console.log("Hello world!");
            
//             return lp;}}
// });
// });