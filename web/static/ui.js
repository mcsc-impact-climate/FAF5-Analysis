import { geojsonTypes, availableGradientAttributes, selectedGradientAttributes, legendLabels, truckChargingOptions, selectedTruckChargingOptions, stateSupportOptions, selectedStateSupportOptions, tcoOptions, selectedTcoOptions, emissionsOptions, selectedEmissionsOptions, gridEmissionsOptions, hourlyEmissionsOptions, selectedHourlyEmissionsOptions, selectedGridEmissionsOptions, faf5Options, selectedFaf5Options, fuelLabels, dataInfo } from './name_maps.js';
import { updateSelectedLayers, updateLegend, updateLayer, data, removeLayer, loadLayer } from './map.js'
import { geojsonNames } from './main.js'

// Mapping of state abbreviations to full state names
const stateNames = {
  'AL': 'Alabama',
  'AK': 'Alaska',
  'AZ': 'Arizona',
  'AR': 'Arkansas',
  'CA': 'California',
  'CO': 'Colorado',
  'CT': 'Connecticut',
  'DE': 'Delaware',
  'FL': 'Florida',
  'GA': 'Georgia',
  'HI': 'Hawaii',
  'ID': 'Idaho',
  'IL': 'Illinois',
  'IN': 'Indiana',
  'IA': 'Iowa',
  'KS': 'Kansas',
  'KY': 'Kentucky',
  'LA': 'Louisiana',
  'ME': 'Maine',
  'MD': 'Maryland',
  'MA': 'Massachusetts',
  'MI': 'Michigan',
  'MN': 'Minnesota',
  'MS': 'Mississippi',
  'MO': 'Missouri',
  'MT': 'Montana',
  'NE': 'Nebraska',
  'NV': 'Nevada',
  'NH': 'New Hampshire',
  'NJ': 'New Jersey',
  'NM': 'New Mexico',
  'NY': 'New York',
  'NC': 'North Carolina',
  'ND': 'North Dakota',
  'OH': 'Ohio',
  'OK': 'Oklahoma',
  'OR': 'Oregon',
  'PA': 'Pennsylvania',
  'RI': 'Rhode Island',
  'SC': 'South Carolina',
  'SD': 'South Dakota',
  'TN': 'Tennessee',
  'TX': 'Texas',
  'UT': 'Utah',
  'VT': 'Vermont',
  'VA': 'Virginia',
  'WA': 'Washington',
  'WV': 'West Virginia',
  'WI': 'Wisconsin',
  'WY': 'Wyoming'
};

function populateLayerDropdown(mapping, mapping_uploaded) {
  const areaLayerDropdown = document.getElementById("area-layer-dropdown");
  const highwayFlowContainer = document.getElementById("highway-flow-checkboxes");
  const highwayInfraContainer = document.getElementById("highway-infra-checkboxes");
  const pointH2prodContainer = document.getElementById("point-h2prod-checkboxes");
  const pointRefuelContainer = document.getElementById("point-refuel-checkboxes");
  const pointOtherContainer = document.getElementById("point-other-checkboxes");
  const uploadedLayerDropdown = document.getElementById("uploaded-layer-dropdown");

  // Clear existing options and checkboxes
  areaLayerDropdown.innerHTML = "";
  highwayFlowContainer.innerHTML = "";
  highwayInfraContainer.innerHTML = "";
  pointH2prodContainer.innerHTML = "";
  pointRefuelContainer.innerHTML = "";
  pointOtherContainer.innerHTML = "";
  uploadedLayerDropdown.innerHTML = "";

  // Make a 'None' option for area feature in case the user doesn't want one
  const option = document.createElement("option");
  option.value = 'None';
  option.textContent = 'None';
  areaLayerDropdown.appendChild(option);
    
  // Add options for area layers
  for (const key in mapping) {
    if (geojsonTypes[key] === "area") {
      const option = document.createElement("option");
      option.value = mapping[key];
      option.textContent = key;
      areaLayerDropdown.appendChild(option);
    } else if (geojsonTypes[key][0] === "highway") {
      // Add checkboxes for highway layers
      if (geojsonTypes[key][1] === "flow") {
      addLayerCheckbox(key, mapping[key], highwayFlowContainer);
      }
      else if (geojsonTypes[key][1] === "infra") {
      addLayerCheckbox(key, mapping[key], highwayInfraContainer);
      }
    } else if (geojsonTypes[key][0] === "point") {
      // Add checkboxes for point layers
      if (geojsonTypes[key][1] === "refuel") {
        addLayerCheckbox(key, mapping[key], pointRefuelContainer);
      }
      else if (geojsonTypes[key][1] === "h2prod") {
      addLayerCheckbox(key, mapping[key], pointH2prodContainer);
      }
      else if (geojsonTypes[key][1] === "other") {
      addLayerCheckbox(key, mapping[key], pointOtherContainer);
      }
    }
  }
    
    // Add options for uploaded layers
    for (const key in mapping_uploaded) {
        const option = document.createElement("option");
        option.value = mapping_uploaded[key];
        option.textContent = key;
        uploadedLayerDropdown.appendChild(option);
    }
}

function addLayerCheckbox(key, value, container) {
  const checkboxContainer = document.createElement("div");
  checkboxContainer.classList.add("checkbox-container"); // Add this line

  const checkbox = document.createElement("input");
  checkbox.type = "checkbox";
  checkbox.value = value;
  checkbox.id = `${key}-checkbox`; // Unique ID for the checkbox
  checkboxContainer.appendChild(checkbox);

  const label = document.createElement("label");
  label.setAttribute("for", `${key}-checkbox`);
  label.textContent = key;
  checkboxContainer.appendChild(label);

  container.appendChild(checkboxContainer);

  // New button creation
  const detailsButton = document.createElement("button");
  detailsButton.textContent = "More";
  detailsButton.setAttribute("data-key", key);
  detailsButton.classList.add("details-btn");
  checkboxContainer.appendChild(detailsButton);
}

function getSelectedLayers() {
  const selectedLayerNames = [];
  const checkboxes = document.querySelectorAll('input[type="checkbox"]');

  // Get selected checkboxes
  checkboxes.forEach((checkbox) => {
    if (checkbox.checked) {
      selectedLayerNames.push(checkbox.nextSibling.textContent); // Get the label text
    }
  });

  // Get the selected area layer from the dropdown
  const areaLayerDropdown = document.getElementById("area-layer-dropdown");
 for (const option of areaLayerDropdown.options) {
    if (option.selected && option.text !== 'None') {
      selectedLayerNames.push(option.text); // Push the text of the selected option
    }
  }
  return selectedLayerNames;
}

const areaLayerDropdown = document.getElementById("area-layer-dropdown");
const details_button = document.getElementById("area-details-button");

areaLayerDropdown.addEventListener('change', function() {
  if (this.value === 'None') {
    details_button.style.visibility = "hidden";
  } else {
    details_button.style.visibility = "visible";
  }
});

function getSelectedLayersValues() {
  const selectedLayerValues = new Map();
  const checkboxes = document.querySelectorAll('input[type="checkbox"]');

  // Get selected checkboxes
  checkboxes.forEach((checkbox) => {
    if (checkbox.checked) {
      // print(checkbox)
      selectedLayerValues.set(checkbox.nextSibling.textContent, checkbox.value); // Get the label text
    }
  });

  // Get the selected area layer from the dropdown
  const areaLayerDropdown = document.getElementById("area-layer-dropdown");
 for (const option of areaLayerDropdown.options) {
    if (option.selected && option.text !== 'None') {
      selectedLayerValues.set(option.text, option.value); // Push the text of the selected option
    }
  }
  return selectedLayerValues;
}

// Add event listener to the parent element of the buttons
document.getElementById("layer-selection").addEventListener("click", function (event) {
  if (event.target.classList.contains("toggle-button")) {
    const targetId = event.target.getAttribute("data-target");
    const target = document.getElementById(targetId);

    if (target.style.display === "none") {
      target.style.display = "block";
    } else {
      target.style.display = "none";
    }
  }
});

// Function to get the selected area layer's name based on its value
function getAreaLayerName(selectedValue) {
  const areaLayerDropdown = document.getElementById("area-layer-dropdown");
  const selectedOption = Array.from(areaLayerDropdown.options).find((option) => option.value === selectedValue);

  return selectedOption ? selectedOption.textContent : "";
}


function getAreaLayerDetails(layerName) {
  // Fetch or compute details related to the 'layerName'.
  // Replace this with your logic to get area layer details.
  // For example, you can fetch data from an API or a database.
  return `Details about ${layerName}`;
}

function createAttributeDropdown(key) {
  // Check if the attribute-dropdown already exists
  if (document.getElementById("attribute-dropdown")) {
    return; // Exit the function if it already exists
  }

  const attributeDropdownContainer = document.createElement("div");
  attributeDropdownContainer.classList.add("attribute-dropdown-container");

  const label = document.createElement("label");
  label.setAttribute("for", "attribute-dropdown");
  label.textContent = "Gradient Attribute: ";

  const attributeDropdown = document.createElement("select");
  attributeDropdown.id = "attribute-dropdown";

  // Assuming you have an array of attribute names for the current feature
  const attributeNames = getAttributeNamesForFeature(key);

  // Create and add options to the dropdown
  attributeNames.forEach((attributeName) => {
    const option = document.createElement("option");
    option.value = attributeName;
    option.text = legendLabels[key][attributeName];
    if (selectedGradientAttributes[key] === attributeName) {
      option.selected = true;
    }
    attributeDropdown.appendChild(option);
  });

  // Add an event listener to the dropdown to handle attribute selection
  attributeDropdown.addEventListener("change", function () {
    selectedGradientAttributes[key] = attributeDropdown.value;
    // Call a function to update the plot and legend with the selected attribute
    updatePlotAndLegend(key);
  });

  // Append the label and dropdown to the container
  attributeDropdownContainer.appendChild(label);
  attributeDropdownContainer.appendChild(attributeDropdown);

  // Append the container to the modal content
  const modalContent = document.querySelector(".modal-content");
  modalContent.appendChild(attributeDropdownContainer);
}

function createDropdown(name, parameter, dropdown_label, key, options_list, selected_options_list, filename_creation_function) {
  const options = options_list[parameter]
  // Check if the dropdown already exists
  if (document.getElementById(name + "-dropdown")) {
    return; // Exit the function if it already exists
  }

  const dropdownContainer = document.createElement("div");
  dropdownContainer.classList.add(name + "-dropdown-container");

  const label = document.createElement("label");
  label.setAttribute("for", name + "-dropdown");
  label.textContent = dropdown_label;

  const dropdown = document.createElement("select");
  dropdown.id = name + "-dropdown";

  // Create and add options to the dropdown
  for (const this_option in options) {
    if (options.hasOwnProperty(this_option)) {
        const option = document.createElement("option");
        option.value = options[this_option]; // Use the key as the value
        option.text = this_option; // Use the corresponding value as the text
        if (selected_options_list[parameter] === option.value) {
            option.selected = true;
        }
        dropdown.appendChild(option);
    }
  }

  // Add an event listener to the dropdown to handle attribute selection
  dropdown.addEventListener("change", async function () {
    selected_options_list[parameter] = dropdown.value;
    await removeLayer(key);
    await loadLayer(key, filename_creation_function(selected_options_list));
    await updateSelectedLayers();
    if (key === "State-Level Incentives and Regulations") {
        for (const fuel_type in legendLabels[key]) {
        legendLabels[key][fuel_type] = convertToTitleCase(selectedStateSupportOptions['Support Target']) + ' ' + convertToTitleCase(selectedStateSupportOptions['Support Type']) + ' (' + fuelLabels[fuel_type] + ')';
        }
    }
    await updateLegend();
  });

  // Append the label and dropdown to the container
  dropdownContainer.appendChild(label);
  dropdownContainer.appendChild(dropdown);

  // Append the container to the modal content
  const modalContent = document.querySelector(".modal-content");
  modalContent.appendChild(dropdownContainer);
}

function convertToTitleCase(str) {
  const words = str.split('_');
  const capitalizedWords = words.map(word => word.charAt(0).toUpperCase() + word.slice(1));
  const titleCaseString = capitalizedWords.join(' ');
  return titleCaseString;
}


function createTruckChargingFilename(selected_options_list) {
  return "Truck_Stop_Parking_Along_Interstate_with_min_chargers_range_" + selected_options_list['Range'] + "_chargingtime_" + selected_options_list['Charging Time'] + "_maxwait_" + selected_options_list['Max Allowed Wait Time'] + ".geojson";
}

function createStateSupportFilename(selected_options_list) {
  return selected_options_list['Support Target'] + "_" + selected_options_list['Support Type'] + ".geojson";
}

function createStateSupportCSVFilename(selected_options_list) {
  return selected_options_list['Support Target'] + "_" + selected_options_list['Support Type'] + ".geojson";
}

function createTcoFilename(selected_options_list) {
  return "costs_per_mile_payload" + selected_options_list['Average Payload'] + "_avVMT" + selected_options_list['Average VMT'] + '_maxChP' + selected_options_list['Max Charging Power'] + ".geojson";
}

function createEmissionsFilename(selected_options_list) {
  return selected_options_list['Visualize By'] + "emissions_per_mile_payload" + selected_options_list['Average Payload'] + "_avVMT" + selected_options_list['Average VMT'] + ".geojson";
}

function createGridEmissionsFilename(selected_options_list) {
  return selected_options_list['Visualize By'] + "_merged.geojson";
}

function createHourlyEmissionsFilename(selected_options_list) {
  return "daily_grid_emission_profile_hour" + selected_options_list['Hour of Day'] + ".geojson";
}

function createFaf5Filename(selected_options_list) {
  return 'mode_truck_commodity_' + selected_options_list['Commodity'] + "_origin_all_dest_all.geojson";
}

function createChargingDropdowns(key) {
  const rangeDropdownResult = createDropdown("range", "Range", "Truck Range: ", key, truckChargingOptions, selectedTruckChargingOptions, createTruckChargingFilename);
  const chargingTimeDropdownResult = createDropdown("chargingTime", "Charging Time", "Charging Time: ", key, truckChargingOptions, selectedTruckChargingOptions, createTruckChargingFilename);
  const maxWaitTimeDropdownResult = createDropdown("maxWaitTime", "Max Allowed Wait Time", "Max Allowed Wait Time: ", key, truckChargingOptions, selectedTruckChargingOptions, createTruckChargingFilename);
}

function createStateSupportDropdowns(key) {
  const supportTypeDropdownResult = createDropdown("support-type", "Support Type", "Support type: ", key, stateSupportOptions, selectedStateSupportOptions, createStateSupportFilename);
  const supportTargetDropdownResult = createDropdown("support-target", "Support Target", "Support target: ", key, stateSupportOptions, selectedStateSupportOptions, createStateSupportFilename);
}

function createTcoDropdowns(key) {
  const payloadDropdownResult = createDropdown("average-payload", "Average Payload", "Average payload: ", key, tcoOptions, selectedTcoOptions, createTcoFilename);
  const vmtDropdownResult = createDropdown("average-vmt", "Average VMT", "Average VMT: ", key, tcoOptions, selectedTcoOptions, createTcoFilename);
  const chargingPowerDropdownResult = createDropdown("charging-power", "Max Charging Power", "Max charging power: ", key, tcoOptions, selectedTcoOptions, createTcoFilename);
}

function createEmissionsDropdowns(key) {
  const payloadDropdownResult = createDropdown("average-payload", "Average Payload", "Average payload: ", key, emissionsOptions, selectedEmissionsOptions, createEmissionsFilename);
  const vmtDropdownResult = createDropdown("average-vmt", "Average VMT", "Average VMT: ", key, emissionsOptions, selectedEmissionsOptions, createEmissionsFilename);
  const visualizeByDropdownResult = createDropdown("visualize-by", "Visualize By", "Visualize by: ", key, emissionsOptions, selectedEmissionsOptions, createEmissionsFilename);
}

function createGridEmissionsDropdowns(key) {
  const visualizeDropdownResult = createDropdown("visualize-by", "Visualize By", "Visualize by: ", key, gridEmissionsOptions, selectedGridEmissionsOptions, createGridEmissionsFilename);
}

function createHourlyEmissionsDropdowns(key) {
  const visualizeDropdownResult = createDropdown("hour-of-day", "Hour of Day", "Hour of day: ", key, hourlyEmissionsOptions, selectedHourlyEmissionsOptions, createHourlyEmissionsFilename);
}

function createFaf5Dropdowns(key) {
  const visualizeDropdownResult = createDropdown("commodity", "Commodity", "Commodity: ", key, faf5Options, selectedFaf5Options, createFaf5Filename);
}

document.body.addEventListener('click', function(event) {
  // Check if a details button was clicked
  if (event.target.classList.contains("details-btn") && event.target.hasAttribute("data-key")) {
    const key = event.target.getAttribute("data-key");

    // Reset the content of the modal
    resetModalContent();

    // Add a link for the user to download the geojson file
    let url = `${STORAGE_URL}${geojsonNames[key]}`
  
    const dirs_with_multiple_geojsons = ['infrastructure_pooling_thought_experiment', 'incentives_and_regulations', 'grid_emission_intensity', 'costs_and_emissions'];
  
    let dir_has_multiple_geojsons = false;
    for (let i = 0; i < dirs_with_multiple_geojsons.length; i++) {
      if (url.includes(dirs_with_multiple_geojsons[i])) {
          dir_has_multiple_geojsons = true;
          break; // Exit the loop once a match is found
      }
    }
    let details_content = '';
    if (dir_has_multiple_geojsons) {
      // Remove the geojson filename from the download url
      const lastSlashIndex = url.lastIndexOf('/');
      const base_directory = url.substring(0, lastSlashIndex);
      
      details_content = dataInfo[key] + '<br><br><a href=' + base_directory + '.zip>Link to download all geojson files</a> used to visualize this layer.';
    }
    else {
      details_content = dataInfo[key] + '<br><br><a href=' + url + '>Link to download the geojson file</a> used to visualize this layer.';
    }
  
    document.getElementById('details-content').innerHTML = details_content;
      
    document.getElementById('details-title').innerText = `${key} Details`;

    // Show the modal
    document.getElementById('details-modal').style.display = 'flex';

    // Create a dropdown menu to choose the gradient attribute
    createAttributeDropdown(key);

    // Create additional dropdown menus for the truck charging layer
    if(key === "Truck Stop Charging") {
        createChargingDropdowns(key);
    }
  }

  // Check if the close button of the modal was clicked
  if (event.target.classList.contains("close-btn")) {//|| event.target.parentElement.tagName === 'SELECT') {
    document.getElementById('details-modal').style.display = 'none';
  }
});


document.getElementById("area-details-button").addEventListener("click", function () {
  const areaLayerDropdown = document.getElementById("area-layer-dropdown");
  const selectedAreaLayer = areaLayerDropdown.value;
  if (selectedAreaLayer !== "") {
    // Fetch details based on the selected area layer
    const selectedAreaLayerName = getAreaLayerName(selectedAreaLayer);

    const details = getAreaLayerDetails(selectedAreaLayer);

    // Reset the content of the modal
    resetModalContent();
      
    // Add a link for the user to download the geojson file
    let url = `${STORAGE_URL}${geojsonNames[selectedAreaLayerName]}`
    
    const dirs_with_multiple_geojsons = ['infrastructure_pooling_thought_experiment', 'incentives_and_regulations', 'grid_emission_intensity', 'costs_and_emissions'];
    
    let dir_has_multiple_geojsons = false;
    for (let i = 0; i < dirs_with_multiple_geojsons.length; i++) {
        if (url.includes(dirs_with_multiple_geojsons[i])) {
            dir_has_multiple_geojsons = true;
            break; // Exit the loop once a match is found
        }
    }
    let details_content = '';
    if (dir_has_multiple_geojsons) {
        // Remove the geojson filename from the download url
        const lastSlashIndex = url.lastIndexOf('/');
        const base_directory = url.substring(0, lastSlashIndex);
        
        details_content = dataInfo[selectedAreaLayerName] + '<br><br><a href=' + base_directory + '.zip>Link to download all geojson files</a> used to visualize this layer.';
    }
    else {
        details_content = dataInfo[selectedAreaLayerName] + '<br><br><a href=' + url + '>Link to download the geojson file</a> used to visualize this layer.';
    }
    
    document.getElementById('details-content').innerHTML = details_content;
      
    document.getElementById('details-title').innerText = `${selectedAreaLayerName} Details`;

    // Show the modal
    document.getElementById('details-modal').style.display = 'flex';

    // Create a dropdown menu to choose attributes for the area layer
    createAttributeDropdown(selectedAreaLayerName);

    // Create a dropdown if needed for state-level incentives and support
    if (selectedAreaLayerName === 'State-Level Incentives and Regulations') {
        createStateSupportDropdowns(selectedAreaLayerName)
    }
    
    // Create a dropdown if needed for state-level TCO
    if (selectedAreaLayerName === 'Total Cost of Truck Ownership') {
        createTcoDropdowns(selectedAreaLayerName)
    }
      
    // Create a dropdown if needed for state-level TCO
    if (selectedAreaLayerName === 'Lifecycle Truck Emissions') {
        createEmissionsDropdowns(selectedAreaLayerName)
    }
    // Create a dropdown to select whether to view grid emission by state or balancing authority
    if(selectedAreaLayerName === "Grid Emission Intensity") {
        createGridEmissionsDropdowns(selectedAreaLayerName);
    }
    // Create a dropdown to select hour of day for hourly grid emissions by ISO
    if(selectedAreaLayerName === "Hourly Grid Emissions") {
        createHourlyEmissionsDropdowns(selectedAreaLayerName);
    }
    // Create a dropdown to select whether to view grid emission by state or balancing authority
    if(selectedAreaLayerName === "Truck Imports and Exports") {
      createFaf5Dropdowns(selectedAreaLayerName);
    }
  }
});


function getAttributeNamesForFeature(layerName) {
  // Check if the layerName exists in availableGradientAttributes
  if (layerName in availableGradientAttributes) {
    return availableGradientAttributes[layerName];
  } else {
    return []; // Return an empty array if the layerName is not found
  }
}

function updatePlotAndLegend(key) {
  updateLayer(key, selectedGradientAttributes[key]);
  updateLegend();
}

// Sample implementation of getDetails function
function getDetails(key) {
  // Fetch or compute details related to the 'key'.
  // For the simplicity of this example, returning a static text.
  //return `Details about ${key}`;
  return '';
}

function resetModalContent() {
  const modalContent = document.querySelector(".modal-content");

  // Remove attribute-dropdown-container if it exists
  const attributeDropdownContainer = document.querySelector(".attribute-dropdown-container");
  if (attributeDropdownContainer) {
    modalContent.removeChild(attributeDropdownContainer);
  }

  // Remove range-dropdown-container if it exists
  const rangeDropdownContainer = document.querySelector(".range-dropdown-container");
  if (rangeDropdownContainer) {
    modalContent.removeChild(rangeDropdownContainer);
  }

  // Remove chargingTime-dropdown-container if it exists
  const chargingTimeDropdownContainer = document.querySelector(".chargingTime-dropdown-container");
  if (chargingTimeDropdownContainer) {
    modalContent.removeChild(chargingTimeDropdownContainer);
  }

  // Remove maxWaitTime-dropdown-container if it exists
  const maxWaitTimeDropdownContainer = document.querySelector(".maxWaitTime-dropdown-container");
  if (maxWaitTimeDropdownContainer) {
    modalContent.removeChild(maxWaitTimeDropdownContainer);
  }

   // Remove support-type-dropdown-container if it exists
  const supportTypeDropdownContainer = document.querySelector(".support-type-dropdown-container");
  if (supportTypeDropdownContainer) {
    modalContent.removeChild(supportTypeDropdownContainer);
  }

  // Remove support-target-dropdown-container if it exists
  const supportTargetDropdownContainer = document.querySelector(".support-target-dropdown-container");
  if (supportTargetDropdownContainer) {
    modalContent.removeChild(supportTargetDropdownContainer);
  }
    
  // Remove payload-dropdown-container if it exists
  const payloadDropdownContainer = document.querySelector(".average-payload-dropdown-container");
  if (payloadDropdownContainer) {
    modalContent.removeChild(payloadDropdownContainer);
  }
    
  // Remove vmt-dropdown-container if it exists
  const vmtDropdownContainer = document.querySelector(".average-vmt-dropdown-container");
  if (vmtDropdownContainer) {
    modalContent.removeChild(vmtDropdownContainer);
  }
    
  // Remove visualize-by-dropdown-container if it exists
  const visualizeByDropdownContainer = document.querySelector(".visualize-by-dropdown-container");
  if (visualizeByDropdownContainer) {
    modalContent.removeChild(visualizeByDropdownContainer);
  }
    
  // Remove hour-of-day-dropdown-container if it exists
  const hourOfDayDropdownContainer = document.querySelector(".hour-of-day-dropdown-container");
  if (hourOfDayDropdownContainer) {
    modalContent.removeChild(hourOfDayDropdownContainer);
  }
    
  // Remove commodity-dropdown-container if it exists
  const commodityDropdownContainer = document.querySelector(".commodity-dropdown-container");
  if (commodityDropdownContainer) {
    modalContent.removeChild(commodityDropdownContainer);
  }

  // Remove visualize-by-dropdown-container if it exists
  const chargingPowerDropdownContainer = document.querySelector(".charging-power-dropdown-container");
  if (chargingPowerDropdownContainer) {
    modalContent.removeChild(chargingPowerDropdownContainer);
  }
}

async function showStateRegulations(stateAbbreviation, properties, layerName) {
  const modal = document.getElementById('regulations-modal');
  const content = document.getElementById('regulations-content');
  const selectedFuelType = selectedGradientAttributes['State-Level Incentives and Regulations'];
  
  const stateName = stateNames[stateAbbreviation] || stateAbbreviation;
  content.querySelector('h1').innerText = `Regulations and Incentives for ${stateName}`;
  content.querySelector('p').innerText = 'Click on targets to view more information.';
  let detailsHtml = '';
/*   for (const key in properties) {
    if (properties.hasOwnProperty(key) && key !== 'geometry') {
      detailsHtml += `<p><strong>${key}</strong>: ${properties[key]}</p>`;
    }
  } */

  // Determine which CSV file(s) to fetch based on the selected layers
  const selectedLayerCombinations = getSelectedLayerCombinations(); // Adjust this function as necessary
  const csvFileNames = selectedLayerCombinations.map(layerCombo => `${layerCombo}.csv`);
  
  const groupedData = {};

  // Fetch and display additional data from the corresponding CSV file(s)
  for (const csvFileName of csvFileNames) {
    try {
      const response = await fetch(`${CSV_URL}${csvFileName}`);
      if (!response.ok) {
        throw new Error(`Network response was not ok: ${response.statusText}`);
      }
      const csvText = await response.text();
      const csvData = Papa.parse(csvText, { header: true }).data;

      // Extract support type and support target from the file name
      const [supportTarget, supportType1] = csvFileName.replace('.csv', '').match(/^(.*)_(.*)$/).slice(1);
      const supportType = supportType1.charAt(0).toUpperCase() + supportType1.slice(1);
      
      // Add support type and support target as columns to each row
      csvData.forEach(row => {
        row.SupportType = supportType;
        row.SupportTarget = supportTarget;
      });

      // Filter the CSV data for the relevant state and fuel type
      let stateData = selectedFuelType === 'all'
        ? csvData.filter(row => row.State === stateName)
        : csvData.filter(row => row.State === stateName && row.Types.split(', ').some(fuel => fuel.toLowerCase().startsWith(selectedFuelType.toLowerCase())));

      // Group data by Support Type and Support Target
      stateData.forEach(row => {
        const supportType = selectedStateSupportOptions['Support Type'] || 'Unknown';
        const supportTarget = selectedStateSupportOptions['Support Target'] || 'Unknown';
        const fuels = row.Types ? row.Types.split(', ') : ['Unknown'];

        const normalizedSupportType = supportType === 'incentives_and_regulations' 
          ? ['Incentives', 'Regulations'] 
          : [supportType.charAt(0).toUpperCase() + supportType.slice(1)];
        const targets = supportTarget === 'all' 
          ? ['fuel_use', 'infrastructure', 'vehicle_purchase'] 
          : [supportTarget];
        const fuelType = selectedFuelType === 'all' 
          ? ['fuel_use', 'infrastructure', 'vehicle_purchase'] 
          : [supportTarget];
        normalizedSupportType.forEach(type => {
          if (!groupedData[type]) {
            groupedData[type] = {};
          }
          targets.forEach(target => {
            if (!groupedData[type][target]) {
              groupedData[type][target] = {};
            }
            fuels.forEach(fuel => {
              if (!groupedData[type][target][fuel]) {
                groupedData[type][target][fuel] = [];
              }
              //console.log(row)
              //groupedData[type][target][fuel].push(row);
              //console.log(type, target, fuel);
              //console.log(row.SupportType, row.SupportTarget, row.Types)
              if (type == row.SupportType & target == row.SupportTarget)
                groupedData[row.SupportType][row.SupportTarget][fuel].push(row);
            });
          });
          //groupedData[row.SupportType][row.SupportTarget][fuel].push(row);
        });
      });

    } catch (error) {
      detailsHtml += `<p>Error loading additional data from ${csvFileName}: ${error.message}</p>`;
    }
  }

// Generate HTML content based on the grouped data
for (const supportType in groupedData) {
  if (Object.keys(groupedData[supportType]).length > 0) {
    let typeContent = ''; // Temporary variable to store the content for this support type
    for (const supportTarget in groupedData[supportType]) {
      let targetContent = ''; // Temporary variable to store the content for this support target
      for (const fuel in groupedData[supportType][supportTarget]) {
        if (groupedData[supportType][supportTarget][fuel].length > 0 && (selectedFuelType === 'all' || fuel.toLowerCase().startsWith(selectedFuelType.toLowerCase()))) {
          let fuelContent = `<h4>${fuel}</h4><div class="fuel-content">`;
          groupedData[supportType][supportTarget][fuel].forEach(row => {
            const nameHtml = row.Types.split(', ').length > 1 
              ? `<i>${row.Name}</i>` 
              : row.Name;
            fuelContent += `<p>${nameHtml}: <a href="${row.Source}" target="_blank">${row.Source}</a></p>`;
          });
          fuelContent += `</div>`;
          targetContent += fuelContent;
        }
        
      }
      if (targetContent) { // Add the support target header and content if there are valid entries
        const supportTarget1 = supportTarget.toLowerCase().replace(/_/g, ' ').replace(/\b\w/g, char => char.toUpperCase());
        typeContent += `<h3 class="collapsible">Target: ${supportTarget1}</h3><div class="content">${targetContent}</div>`;
      }
    }
    if (typeContent) { // Add the support type header and content if there are valid entries
      detailsHtml += `<h2><ins>${supportType}</ins></h2>${typeContent}`;
    }
  }
}

// Set the inner HTML
content.innerHTML = `
  <span class="close-regulations">&times;</span>
  <h1>Regulations and Incentives for ${stateName}</h1>
  <p>Click on targets to view more information.</p>
  ${detailsHtml}
  <p><em>Italicized regulations and incentives benefit multiple fuel types and appear multiple times.</em></p>
`;
modal.style.display = 'flex';

const closeButton = modal.querySelector('.close-regulations');
closeButton.onclick = function() {
  modal.style.display = 'none';
};

// Add collapsible functionality to only h3 elements
document.querySelectorAll('h3.collapsible').forEach((header) => {
  header.addEventListener('click', function() {
    this.classList.toggle('active');
    const content = this.nextElementSibling;
    if (content.style.display === 'block') {
      content.style.display = 'none';
    } else {
      content.style.display = 'block';
    }
  });
});
}


function getSelectedLayerCombinations() {
  const supportType = selectedStateSupportOptions['Support Type'];
  const supportTarget = selectedStateSupportOptions['Support Target'];

  //console.log('hi')
  //console.log(selectedStateSupportOptions)

  const combinations = [];

  // Define your logic to map selected layers to CSV file names
  // For example:
  if (supportType == 'incentives') {
    if (supportTarget == 'fuel_use') {
      combinations.push('fuel_use_incentives');
    }
    else if (supportTarget == 'infrastructure') {
      combinations.push('infrastructure_incentives');
    }
    else if (supportTarget == 'vehicle_purchase') {
      combinations.push('vehicle_purchase_incentives');
    }
    else if (supportTarget == 'all') {
      combinations.push('fuel_use_incentives');
      combinations.push('infrastructure_incentives');
      combinations.push('vehicle_purchase_incentives');
    }
  } else if (supportType == 'regulations') {
    if (supportTarget == 'fuel_use') {
      combinations.push('fuel_use_regulations');
    }
    else if (supportTarget == 'infrastructure') {
      combinations.push('infrastructure_regulations');
    }
    else if (supportTarget == 'vehicle_purchase') {
      combinations.push('vehicle_purchase_regulations');
    }
    else if (supportTarget == 'all') {
      combinations.push('fuel_use_regulations');
      combinations.push('infrastructure_regulations');
      combinations.push('vehicle_purchase_regulations');
    }
  }
  else if (supportType == 'incentives_and_regulations'){
    if (supportTarget == 'fuel_use') {
      combinations.push('fuel_use_regulations');
      combinations.push('fuel_use_incentives');
    }
    else if (supportTarget == 'infrastructure') {
      combinations.push('infrastructure_regulations');
      combinations.push('infrastructure_incentives');
    }
    else if (supportTarget == 'vehicle_purchase') {
      combinations.push('vehicle_purchase_regulations');
      combinations.push('vehicle_purchase_incentives');
    }
    else if (supportTarget == 'all') {
      combinations.push('fuel_use_regulations');
      combinations.push('fuel_use_incentives');
      combinations.push('infrastructure_regulations');
      combinations.push('infrastructure_incentives');
      combinations.push('vehicle_purchase_regulations');
      combinations.push('vehicle_purchase_incentives');
    }
  }
    //(combinations[0])
    return combinations;
}



export { populateLayerDropdown, getSelectedLayers, getSelectedLayersValues, showStateRegulations, getAreaLayerName};
