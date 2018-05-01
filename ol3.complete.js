// START Matt Walker's code
// Extent of the map in units of the projection (these match our base map)
var extent = [646.36 308975.28
276050.82 636456.31];

// Fixed resolutions to display the map at (pixels per ground unit (meters when
// the projection is British National Grid))
var resolutions = [1600,800,400,200,100,50,25,10,5,2.5,1,0.5,0.25,0.125,0.0625];

// Define British National Grid Proj4js projection (copied from http://epsg.io/28992.js)
proj4.defs(proj4.defs("EPSG:28992","+proj=sterea +lat_0=52.15616055555555 +lon_0=5.38763888888889 +k=0.9999079 +x_0=155000 +y_0=463000 +ellps=bessel +towgs84=565.417,50.3319,465.552,-0.398957,0.343988,-1.8774,4.0725 +units=m +no_defs");

// Define an OL3 projection based on the included Proj4js projection
// definition and set it's extent.
var bng = ol.proj.get('EPSG:27700');
bng.setExtent(extent);

// Define a TileGrid to ensure that WMS requests are made for
// tiles at the correct resolutions and tile boundaries
var tileGrid = new ol.tilegrid.TileGrid({
	origin: extent.slice(0, 2),
	resolutions: resolutions
});

var map = new ol.Map({
	target: 'map',
	layers: [
		new ol.layer.Tile({
			source: new ol.source.TileWMS({
				url: 'http://yourserver/geoserver/base/wms?',
				attributions: [
					new ol.Attribution({html: 'Angus Council 100023404 &copy; Ordnance Survey'})
				],
				params: {
					'LAYERS': 'oslayers',
					'FORMAT': 'image/png',
					'TILED': true
				},
				tileGrid: tileGrid
			})
		})
	],
	view: new ol.View({
		projection: bng,
		resolutions: resolutions,
		center: [350000, 750000],
		zoom: 5
	}),
	controls: ol.control.defaults({
	  attributionOptions: {
		collapsible: false
	  }
	})
});

// END Matt Walker's code
// START pgRouting workshop code
// pgRouting layer values
// This is the layer you created in Ch. 9 of the pgRouting workshop
var params = {
	'LAYERS': 'pgrouting:pgrouting',
	'FORMAT': 'image/png'
};

// The "start" and "destination" features.
var startPoint = new ol.Feature();
var destPoint = new ol.Feature();

// The vector layer used to display the "start" and "destination" features.
var vectorLayer = new ol.layer.Vector({
  source: new ol.source.Vector({
	features: [startPoint, destPoint]
  })
});
map.addLayer(vectorLayer);

// Note changes to EPSG:27700 from EPSG:4326 and EPSG:3857
// This bit could probably be removed
// A transform function to convert coordinates from EPSG:27700
// to EPSG:27700.
var transform = ol.proj.getTransform('EPSG:27700', 'EPSG:27700');

// Register a map click listener.
map.on('click', function(event) {
  if (startPoint.getGeometry() == null) {
	// First click.
	startPoint.setGeometry(new ol.geom.Point(event.coordinate));
  } else if (destPoint.getGeometry() == null) {
	// Second click.
	destPoint.setGeometry(new ol.geom.Point(event.coordinate));
	// Transform the coordinates from the map projection (EPSG:27700)
	// to the server projection (EPSG:27700).
	var startCoord = transform(startPoint.getGeometry().getCoordinates());
	var destCoord = transform(destPoint.getGeometry().getCoordinates());
	var viewparams = [
	  'x1:' + startCoord[0], 'y1:' + startCoord[1],
	  'x2:' + destCoord[0], 'y2:' + destCoord[1]
	];
	params.viewparams = viewparams.join(';');
	result = new ol.layer.Image({
	  source: new ol.source.ImageWMS({
		url: 'http://yourserver/geoserver/routing/wms?',	// URL of your 27700 WMS
		params: params
	  })
	});
	map.addLayer(result);
  }
});

var clearButton = document.getElementById('clear');
clearButton.addEventListener('click', function(event) {
  // Reset the "start" and "destination" features.
  startPoint.setGeometry(null);
  destPoint.setGeometry(null);
  // Remove the result layer.
  map.removeLayer(result);
});	
// END pgRouting workshop code