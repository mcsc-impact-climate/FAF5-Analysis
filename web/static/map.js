import { createStyleFunction, isPolygonLayer, isPointLayer, isLineStringLayer } from './styles.js';
import { getSelectedLayers, getSelectedLayersValues, showStateRegulations, getAreaLayerName } from './ui.js';
import { legendLabels, selectedGradientAttributes, geojsonColors, selectedGradientTypes } from './name_maps.js';

var vectorLayers = [];
var map;
var attributeBounds = {}; // Object to store min and max attribute values for each geojson

// Declare the data variable in a higher scope
let data;

function initMap() {
  map = new ol.Map({
    target: 'map',
    layers: [
      new ol.layer.Tile({
        source: new ol.source.OSM(),
      }),
      ...vectorLayers.filter(layer => isPolygonLayer(layer)),  // Add polygon layers first
      ...vectorLayers.filter(layer => isLineStringLayer(layer)), // Add LineString layers next
      ...vectorLayers.filter(layer => isPointLayer(layer))    // Add point layers last
    ],
    view: new ol.View({
      center: ol.proj.fromLonLat([-98, 39]), // Centered on the US
      zoom: 4.5,
    }),
  });

    // Set the visibility of all vector layers to false initially
  vectorLayers.forEach((layer) => {
    layer.setVisible(false);
    
  });
  map.on('pointermove', handleMapHover);
  map.on('singleclick', handleMapClick);
  let lastFeature = null;

}

// Attach the updateSelectedLayers function to the button click event
async function attachEventListeners() {
  const applyButton = document.getElementById("apply-button");
  applyButton.addEventListener('click', async () => {
    await updateSelectedLayers(); // Wait for updateSelectedLayers to complete
    updateLegend(); // Now, call updateLegend after updateSelectedLayers is done
  });

  const uploadedLayerDropdown = $('#uploaded-layer-dropdown');
  console.log(uploadedLayerDropdown); // This should not be null or undefined
  if (uploadedLayerDropdown.length > 0) {
    // Initialize select2 if not already done
    uploadedLayerDropdown.select2({
      placeholder: 'Select one or more layers',
      allowClear: true
    });

    // Use select2's specific events for handling changes
    uploadedLayerDropdown.on('select2:select select2:unselect', async () => {
      console.log('Uploaded layer dropdown change detected via select2');
      await updateUploadedLayers(); // Call function to update layers based on uploaded files
      updateLegend(); // Update the legend to include uploaded layers
    });
  } else {
    console.error('uploaded-layer-dropdown not found in the DOM');
  }
}

let lastFeature;

// Function to handle hover events
function handleMapHover(event) {
  let featureFound = false;
  map.forEachFeatureAtPixel(event.pixel, function(feature) {
    featureFound = true;
    //console.log(getAreaLayerName(document.getElementById("area-layer-dropdown").value));
    if (feature !== lastFeature && getAreaLayerName(document.getElementById("area-layer-dropdown").value) == 'State-Level Incentives and Regulations') {
      if (lastFeature) {
        const lastLayerName = getAreaLayerName(document.getElementById("area-layer-dropdown").value);
        lastFeature.setStyle(createStyleFunction(lastLayerName, 'gray', 1)); // Reset style on the last hovered feature
      }
      if (feature) {
        const currentLayerName = feature.get('layerName');
        //console.log('Current Layer Name:', currentLayerName); // Debugging
        feature.setStyle(createStyleFunction(currentLayerName, 'white', 3, true)); // Apply hover style to the new feature
      }
      //console.log(getAreaLayerName(document.getElementById("area-layer-dropdown").value));
      lastFeature = feature;
    }
  });
  // If no feature was found under the cursor, reset the last hovered feature, if goes off map, last hovered feature does not stay color
  if (!featureFound && lastFeature) {
    const lastLayerName = 'State-Level Incentives and Regulations'; // Adjust as needed
    lastFeature.setStyle(createStyleFunction(lastLayerName, 'gray', 1)); // Reset the last feature's style
    lastFeature = null; // Clear lastFeature to avoid retaining hover effects
  }
}


// Function to handle click events
function handleMapClick(event) {
  map.forEachFeatureAtPixel(event.pixel, function(feature) {
    const layerName = getAreaLayerName(document.getElementById("area-layer-dropdown").value) //feature.get('layerName'); //not sure if this is correct
    if (layerName == 'State-Level Incentives and Regulations') {
      if (feature) {
        const properties = feature.getProperties();
        const stateAbbreviation = properties.STUSPS || properties.state || properties.STATE;
        //console.log(layerName);
        if (stateAbbreviation) {
          showStateRegulations(stateAbbreviation, properties, layerName);
        } else {
          console.log('State abbreviation not found in feature properties');
        }
      }
    }
  });
}



// Initialize an empty layer cache
const layerCache = {};

// Function to compare two layers based on their geometry types
function compareLayers(a, b) {
  const layer1 = layerCache[a];
  const layer2 = layerCache[b];

  if (isPolygonLayer(layer1) && !isPolygonLayer(layer2)) {
    return -1; // layer1 is a polygon layer, layer2 is not
  } else if (!isPolygonLayer(layer1) && isPolygonLayer(layer2)) {
    return 1; // layer2 is a polygon layer, layer1 is not
  } else if (isLineStringLayer(layer1) && !isLineStringLayer(layer2)) {
    return -1; // layer1 is a line layer, layer2 is not
  } else if (!isLineStringLayer(layer1) && isLineStringLayer(layer2)) {
    return 1; // layer2 is a line layer, layer1 is not
  } else if (isPointLayer(layer1) && !isPointLayer(layer2)) {
    return -1; // layer1 is a point layer, layer2 is not
  } else if (!isPointLayer(layer1) && isPointLayer(layer2)) {
    return 1; // layer2 is a point layer, layer1 is not
  } else {
    return 0; // both layers have the same geometry type
  }
}

// Function to load a specific layer from the server
async function loadLayer(layerName, filename='') {
  const layerMap=getSelectedLayersValues();
//  console.log(layerMap.get(layerName))

  // Construct the URL without the "geojsons/" prefix
  //const url = `/get_geojson/${layerName}`;
  let url = `${STORAGE_URL}${layerMap.get(layerName)}`

  console.log(url)
  // If needed, update the filename in the url
  if (filename !== '') {
    const lastSlashIndex = url.lastIndexOf('/');
    const dir = url.substring(0, lastSlashIndex + 1);
    url = dir + filename;
    console.log(url)
  }

  let spinner = document.getElementById('lds-spinner')
  try {
    spinner.style.visibility= "visible"
    const response = await fetch(url);
    if (!response.ok) {
      spinner.style.visibility= "hidden"
      throw new Error('Network response was not ok');
    }

    const geojsonData = await response.json();
    const features = new ol.format.GeoJSON().readFeatures(geojsonData, {
      dataProjection: 'EPSG:3857',
      featureProjection: 'EPSG:3857',
    });
    
    const attributeKey = layerName;
    let attributeName = '';
    if (layerName in selectedGradientAttributes) {
        attributeName = selectedGradientAttributes[attributeKey];
        const minVal = Math.min(...features.map(f => f.get(attributeName) || Infinity));
        const maxVal = Math.max(...features.map(f => f.get(attributeName) || -Infinity));

        attributeBounds[layerName] = { min: minVal, max: maxVal };
    }

    // Create a vector layer for the selected layer and add it to the map
    const vectorLayer = new ol.layer.Vector({
      source: new ol.source.Vector({
        features: features,
      }),
      style: createStyleFunction(layerName),
      key: layerName.split(".")[0], // Set the key property with the geojson name without extension
    });

    // Add the layer to the map and cache it
    layerCache[layerName] = vectorLayer;
    vectorLayers.push(vectorLayer);
    spinner.style.visibility= "hidden"
  } catch (error) {
    console.log('Fetch Error:', error);
    spinner.style.visibility= "hidden"
    throw error; // Propagate the error
  }
}

function removeLayer(layerName) {
  // Find the layer by its name
  const layerIndex = vectorLayers.findIndex(layer => layer.get("key").split(".")[0] === layerName);

  if (layerIndex !== -1) {
    // Remove the layer from the map
    map.removeLayer(vectorLayers[layerIndex]);

    // Remove the layer from the vectorLayers array
    vectorLayers.splice(layerIndex, 1);

    // Remove the layer from the cache
    delete layerCache[layerName];
  }
}

// Function to update a specific layer with a new attributeName
async function updateLayer(layerName, attributeName) {

  // Check if the layerName is cached
  if (!layerCache[layerName]) {
    // If the layer is not in the cache, load it using loadLayer
    await loadLayer(layerName);
  }

  // Update the attributeName and style for the layer
  const vectorLayer = layerCache[layerName];
  vectorLayer.setStyle(createStyleFunction(layerName, attributeName)); // Pass the new attributeName

  // Update the attributeBounds for the layer if needed
  const attributeKey = layerName;
  if (layerName in selectedGradientAttributes) {
    const minVal = Math.min(...vectorLayer.getSource().getFeatures().map(f => f.get(attributeName) || Infinity));
    const maxVal = Math.max(...vectorLayer.getSource().getFeatures().map(f => f.get(attributeName) || -Infinity));
    attributeBounds[layerName] = { min: minVal, max: maxVal };
  }

}

function setLayerVisibility(layerName, isVisible) {
  // Find the layer by its name and update its visibility
  const layer = vectorLayers.find(layer => layer.get("key").split(".")[0] === layerName);

  if (layer) {
    layer.setVisible(isVisible);
  }
}

// Function to update the selected layers on the map
async function updateSelectedLayers() {
  const selectedLayers = getSelectedLayers();

  // Create an array of promises for loading layers
  const loadingPromises = [];

  // Iterate through the selected layers
  for (const layerName of selectedLayers) {
    if (!layerCache[layerName]) {
      // Push the promise returned by loadLayer into the array
        loadingPromises.push(loadLayer(layerName));

    } else {
      // Layer is in the cache; update its visibility
      setLayerVisibility(layerName, true);
    }
  }

  try {
    // Wait for all loading promises to complete before proceeding
    await Promise.all(loadingPromises);

    // Reorder selectedLayers based on the associated layers in layerCache
    selectedLayers.sort((a, b) => compareLayers(a, b));

    // Hide layers that are not in the selectedLayers list
    Object.keys(layerCache).forEach(attributeKey => {
      if (!selectedLayers.includes(attributeKey)) {
        setLayerVisibility(attributeKey, false);
      }
    });
  } catch (error) {
    // Handle errors if any loading promise fails
    console.error('Error loading layers:', error);
  }

  // Clear all layers from the map except for the base layer
  const baseLayer = map.getLayers().item(0); // Assuming the base layer is the first layer
  map.getLayers().clear();

  // Re-add the base layer to the map
  if (baseLayer) {
    map.addLayer(baseLayer);
  }

  // Add the selected layers to the map
  for (const layerName of selectedLayers) {
        map.addLayer(layerCache[layerName]);
  }
}

// DMM: I don't think this function will actually work quite as intended, needs to be debugged //
async function updateUploadedLayers() {
  console.log("Called updateUploadedLayers")
  const uploadedLayerDropdown = document.getElementById("uploaded-layer-dropdown");
  const selectedLayers = Array.from(uploadedLayerDropdown.selectedOptions).map(option => option.value);
  console.log(selectedLayers)

  const loadingPromises = [];
  console.log(layerCache)

  // Iterate through the selected uploaded layers
  for (const layerName of selectedLayers) {
    console.log(layerName)
    if (!layerCache[layerName]) {
      // Push the promise returned by loadLayer into the array
      console.log("Running loadLayer")
      loadingPromises.push(loadLayer(layerName, layerName));
    } else {
      // Layer is in the cache; update its visibility
      setLayerVisibility(layerName, true);
    }
  }

  try {
    // Wait for all loading promises to complete before proceeding
    await Promise.all(loadingPromises);

    // Hide layers that are not in the selectedLayers list
    Object.keys(layerCache).forEach(attributeKey => {
      if (!selectedLayers.includes(attributeKey)) {
        setLayerVisibility(attributeKey, false);
      }
    });
  } catch (error) {
    // Handle errors if any loading promise fails
    console.error('Error loading uploaded layers:', error);
  }

  // Clear all layers from the map except for the base layer
  const baseLayer = map.getLayers().item(0); // Assuming the base layer is the first layer
  map.getLayers().clear();

  // Re-add the base layer to the map
  if (baseLayer) {
    map.addLayer(baseLayer);
  }

  // Add the selected uploaded layers to the map
  for (const layerName of selectedLayers) {
    map.addLayer(layerCache[layerName]);
  }
}
// ------------------------------------------------------------------------------------------  //

function updateLegend() {
  const legendDiv = document.getElementById("legend");
  legendDiv.style.display = "flex";
  legendDiv.style.flexDirection = "column";

  // Clear existing legend entries
  while (legendDiv.firstChild) {
    legendDiv.removeChild(legendDiv.firstChild);
  }

  // Add and style Legend header
  const header = document.createElement('h3');
  header.appendChild(document.createTextNode('Legend'));
  header.style.fontWeight = "bold";
  legendDiv.appendChild(header);

  // Get the currently selected layers
  const selectedLayers = getSelectedLayers();

  // Iterate through the vectorLayers and update the legend
  vectorLayers.forEach((layer) => {
    const layerName = layer.get("key"); // Get the key property

    // Check if this layer is in the list of selected layers or if "All Layers" is selected
    if (selectedLayers.includes(layerName) || selectedLayers.includes("all")) {
      const layerDiv = document.createElement("div");
      layerDiv.style.display = "flex";
      layerDiv.style.alignItems = "center";

      const symbolLabelContainer = document.createElement("div");
      symbolLabelContainer.style.display = "flex";
      symbolLabelContainer.style.width = "150px";  // Setting fixed width to ensure alignment
      symbolLabelContainer.style.alignItems = "center";
      symbolLabelContainer.style.justifyContent = "center";

      const symbolContainer = document.createElement("div");
      symbolContainer.style.display = "flex";
      symbolContainer.style.alignItems = "center";
      symbolContainer.style.width = "120px"; // fixed width

      const canvas = document.createElement("canvas");
      canvas.width = 50;
      canvas.height = 10;
      const ctx = canvas.getContext("2d");

      const useGradient = layerName in selectedGradientAttributes;
      const layerColor = geojsonColors[layerName] || 'blue'; // Fetch color from dictionary, or default to blue
      let attributeName = '';
      let gradientType = '';
      if (useGradient) {
          attributeName = selectedGradientAttributes[layerName];
          gradientType = selectedGradientTypes[layerName];
      }
      const bounds = attributeBounds[layerName];

      // Add legend entry only for visible layers
      if (isPolygonLayer(layer)) {
        if (useGradient ) {
          const minVal = bounds.min < 0.01 ? bounds.min.toExponential(1) : (bounds.min > 100 ? bounds.min.toExponential(1) : bounds.min.toFixed(1));
          const minDiv = document.createElement("div");
          minDiv.innerText = minVal.toString();
          minDiv.style.marginRight = "5px";
          symbolContainer.appendChild(minDiv);
          symbolContainer.style.marginRight = "40px";

          const gradient = ctx.createLinearGradient(0, 0, 50, 0);
          gradient.addColorStop(0, "rgb(255, 255, 255)");
          gradient.addColorStop(1, `rgb(255, 0, 0)`);
          ctx.fillStyle = gradient;
          ctx.fillRect(0, 0, 50, 10);
          symbolContainer.appendChild(canvas);
          symbolContainer.style.marginRight = "40px";

          const maxVal = bounds.max < 0.01 ? bounds.max.toExponential(1) : (bounds.max > 100 ? bounds.max.toExponential(1) : bounds.max.toFixed(1));
          const maxDiv = document.createElement("div");
          maxDiv.innerText = maxVal.toString();
          maxDiv.style.marginLeft = "5px";
          symbolContainer.appendChild(maxDiv);
          symbolContainer.style.marginRight = "40px";
        } else {
          // Solid color rectangle
          ctx.fillStyle = layerColor;
          ctx.fillRect(0, 0, 50, 10);
          symbolContainer.appendChild(canvas);
          symbolContainer.style.marginRight = "40px";
        }
      } else if (isLineStringLayer(layer)) {
        if (useGradient && bounds) { // Check to make sure bounds are actually defined
          const minVal = bounds.min < 0.01 ? bounds.min.toExponential(1) : (bounds.min > 100 ? bounds.min.toExponential(1) : bounds.min.toFixed(1));
          const minDiv = document.createElement("div");
          minDiv.innerText = minVal.toString(); // Minimum attribute value
          minDiv.style.marginRight = "5px";
          symbolContainer.appendChild(minDiv);
          symbolContainer.style.marginRight = "40px";

          // New canvas for line width
          const canvas = document.createElement("canvas");
          canvas.width = 50;
          canvas.height = 20; // Increased height to make space for the varying line width
          const ctx = canvas.getContext("2d");

          // Draw a line segment that gradually increases in width from 1 to 10
          let yPosition = 10; // vertical position for the line

          for (let x = 0; x <= 50; x++) {
            let lineWidth = 1 + (x / 50) * 9; // lineWidth will vary between 1 and 10
            ctx.strokeStyle = layerColor;
            ctx.lineWidth = lineWidth;

            ctx.beginPath();
            ctx.moveTo(x, yPosition - lineWidth / 2);
            ctx.lineTo(x, yPosition + lineWidth / 2);
            ctx.stroke();
          }

          symbolContainer.appendChild(canvas);
          symbolContainer.style.marginRight = "40px";

          // Check to make sure bounds are actually defined
          const maxVal = bounds.max < 0.01 ? bounds.max.toExponential(1) : (bounds.max > 100 ? bounds.max.toExponential(1) : bounds.max.toFixed(1));
          const maxDiv = document.createElement("div");
          maxDiv.innerText = maxVal.toString(); // Maximum attribute value
          maxDiv.style.marginLeft = "5px";
          symbolContainer.appendChild(maxDiv);
          symbolContainer.style.marginRight = "40px";
        } else {
          // New canvas for constant width line
          const constantCanvas = document.createElement("canvas");
          constantCanvas.width = 50;
          constantCanvas.height = 10;  // Set height to 10 for constant line width
          const constantCtx = constantCanvas.getContext("2d");

          constantCtx.strokeStyle = layerColor;
          constantCtx.lineWidth = 3;

          constantCtx.beginPath();
          constantCtx.moveTo(0, 5);
          constantCtx.lineTo(50, 5);
          constantCtx.stroke();

          symbolContainer.appendChild(constantCanvas);
          symbolContainer.style.marginRight = "40px";
        }
      } else if (isPointLayer(layer)) { // this block is for point-like geometries
        // check if gradient should be used for points
        if (useGradient && bounds) {
          if (gradientType === 'size') {
              // Minimum value and minimum point size
              const minVal = bounds.min < 0.01 ? bounds.min.toExponential(1) : (bounds.min > 100 ? bounds.min.toExponential(1) : bounds.min.toFixed(1));
              const minDiv = document.createElement("div");
              minDiv.innerText = minVal.toString();
              minDiv.style.marginRight = "5px";
              symbolContainer.appendChild(minDiv);

              // Canvas to draw points
              const minPointSize = 2;  // Minimum size (can set according to your needs)
              const maxPointSize = 10; // Maximum size (can set according to your needs)

              // Create canvas for the minimum point size
              const minPointCanvas = document.createElement("canvas");
              minPointCanvas.width = 20;
              minPointCanvas.height = 20;
              const minCtx = minPointCanvas.getContext("2d");

              minCtx.fillStyle = layerColor;
              minCtx.beginPath();
              minCtx.arc(10, 10, minPointSize, 0, Math.PI * 2);
              minCtx.fill();
              symbolContainer.appendChild(minPointCanvas);

              // Create canvas for the maximum point size
              const maxPointCanvas = document.createElement("canvas");
              maxPointCanvas.width = 20;
              maxPointCanvas.height = 20;
              const maxCtx = maxPointCanvas.getContext("2d");

              maxCtx.fillStyle = layerColor;
              maxCtx.beginPath();
              maxCtx.arc(10, 10, maxPointSize, 0, Math.PI * 2);
              maxCtx.fill();
              symbolContainer.appendChild(maxPointCanvas);

              // Maximum value
              const maxVal = bounds.max < 0.01 ? bounds.max.toExponential(1) : (bounds.max > 100 ? bounds.max.toExponential(1) : bounds.max.toFixed(1));
              const maxDiv = document.createElement("div");
              maxDiv.innerText = maxVal.toString();
              maxDiv.style.marginLeft = "5px";
              symbolContainer.appendChild(maxDiv);
          }
          else if (gradientType === 'color') {
              // Minimum value and minimum point size
              const minVal = bounds.min < 0.01 ? bounds.min.toExponential(1) : (bounds.min > 100 ? bounds.min.toExponential(1) : bounds.min.toFixed(1));
              const minDiv = document.createElement("div");
              minDiv.innerText = minVal.toString();
              minDiv.style.marginRight = "5px";
              symbolContainer.appendChild(minDiv);

              // Canvas to draw points
              const minPointColor = 'blue';  // Color for minimum value
              const maxPointColor = 'red'; // Color for maximum value

              // Create canvas for the minimum point size
              const minPointCanvas = document.createElement("canvas");
              minPointCanvas.width = 20;
              minPointCanvas.height = 20;
              const minCtx = minPointCanvas.getContext("2d");

              minCtx.fillStyle = minPointColor;
              minCtx.beginPath();
              minCtx.arc(10, 10, 3, 0, Math.PI * 2);
              minCtx.fill();
              symbolContainer.appendChild(minPointCanvas);

              // Create canvas for the maximum point size
              const maxPointCanvas = document.createElement("canvas");
              maxPointCanvas.width = 20;
              maxPointCanvas.height = 20;
              const maxCtx = maxPointCanvas.getContext("2d");

              maxCtx.fillStyle = maxPointColor;
              maxCtx.beginPath();
              maxCtx.arc(10, 10, 3, 0, Math.PI * 2);
              maxCtx.fill();
              symbolContainer.appendChild(maxPointCanvas);

              // Maximum value
              const maxVal = bounds.max < 0.01 ? bounds.max.toExponential(1) : (bounds.max > 100 ? bounds.max.toExponential(1) : bounds.max.toFixed(1));
              const maxDiv = document.createElement("div");
              maxDiv.innerText = maxVal.toString();
              maxDiv.style.marginLeft = "5px";
              symbolContainer.appendChild(maxDiv);
          }
        } else {
          // code for constant size points
          ctx.fillStyle = layerColor;
          ctx.beginPath();
          ctx.arc(25, 5, 3, 0, Math.PI * 2);
          ctx.fill();
          canvas.style.marginLeft = "30px";  // Shift canvas to align the center
          symbolContainer.appendChild(canvas);
        }

        symbolContainer.style.marginRight = "40px";
      }

      layerDiv.appendChild(symbolContainer);

      symbolLabelContainer.appendChild(symbolContainer);  // Append symbolContainer to symbolLabelContainer

      const title = document.createElement("div");

      if (layerName in legendLabels) {
        if (typeof legendLabels[layerName] === 'string') {
          title.innerText = legendLabels[layerName];
        }
        else if (isDictionary(legendLabels[layerName])) {
          title.innerText = legendLabels[layerName][selectedGradientAttributes[layerName]];
        }
        } else {
        title.innerText = layerName;
        }
      title.style.marginLeft = "20px";

      layerDiv.appendChild(symbolLabelContainer);  // Append symbolLabelContainer to layerDiv
      layerDiv.appendChild(title);
      legendDiv.appendChild(layerDiv);
    }
  });
}

async function fetchCSVData(csvFileName) {
  const csvUrl = `${CSV_URL}${csvFileName}`;
  console.log(`Fetching CSV from URL: ${csvUrl}`); // Debug logging
  try {
    const response = await fetch(csvUrl);
    if (!response.ok) {
      throw new Error(`Network response was not ok for ${csvUrl}`);
    }
    const csvText = await response.text();
    return csvText;
  } catch (error) {
    console.error('Fetch CSV Error:', error);
    throw error;
  }
}

function isDictionary(obj) {
  // Check if it's an object
  if (typeof obj !== 'object' || obj === null || Array.isArray(obj)) {
    return false;
  }

  // Check if it has properties (key-value pairs)
  for (const key in obj) {
    if (obj.hasOwnProperty(key)) {
      return true;
    }
  }

  return false;
}

// Add event listener to the "Clear" button
document.getElementById("clear-button").addEventListener("click", function () {
  // Clear all vector layers (excluding the base layer)
  const mapLayers = map.getLayers().getArray();
  mapLayers.forEach(layer => {
    if (layer instanceof ol.layer.Vector && !layer.get("baseLayer")) {
      map.removeLayer(layer);
    }
  });

  // Optionally, clear any selected checkboxes or dropdown selections
  clearLayerSelections();
});

function clearLayerSelections() {
  // Clear selected checkboxes
  const checkboxes = document.querySelectorAll('input[type="checkbox"]');
  checkboxes.forEach(checkbox => {
    checkbox.checked = false;
  });

  // Clear selected option in the area layer dropdown
  const areaLayerDropdown = document.getElementById("area-layer-dropdown");
  areaLayerDropdown.selectedIndex = 0; // Assuming the first option is "Select Area Feature"
  updateSelectedLayers();
  updateLegend();
}

export { initMap, updateSelectedLayers, updateLegend, attachEventListeners, updateLayer, attributeBounds, data, removeLayer, loadLayer, handleMapClick, handleMapHover, map, fetchCSVData };
