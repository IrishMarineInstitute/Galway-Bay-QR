function tide(string, ID) {
        const input = document.getElementById(ID);
        var tide = parseFloat(string).toFixed(2)
        if ( isNaN(tide) ) {
            input.style.backgroundColor = "#8B8000"
            input.style.color = "#FFFFFF"
            input.style.fontSize = "11px"
            // This is to delete units in "DRY" label
            input.value = input.value.slice(0, 8);		
        } else if ( tide >= 5.5 ) {
            input.style.backgroundColor = "#FF0000"
            input.style.color = "#FFFFFF"
        } else {
            input.style.backgroundColor = "#39E75F"
            input.style.color = "#000000"
        }
     }
     
function temperature(string, ID) {
        const input = document.getElementById(ID);
        var temperature = parseFloat(string).toFixed(2)
        if ( isNaN(temperature) ) {
            input.style.backgroundColor = "#8B8000"
            input.style.color = "#FFFFFF"
            input.style.fontSize = "11px"
            // This is to delete units in "DRY" label
            input.value = input.value.slice(0, 8);		
        } else if ( temperature >= 20 ) {
            input.style.backgroundColor = "#FF0000"
            input.style.color = "#FFFFFF"
        } else {
            input.style.backgroundColor = "#39E75F"
            input.style.color = "#000000"
        }
     }
     
function salinity(string, ID) {
        const input = document.getElementById(ID);
        var salinity = parseFloat(string).toFixed(2)
        if ( isNaN(salinity) ) {
            input.style.backgroundColor = "#8B8000"
            input.style.color = "#FFFFFF"
            input.style.fontSize = "11px"
        } else if ( salinity >= 30 ) {
            input.style.backgroundColor = "#006505"
            input.style.color = "#FFFFFF"
        } else if ( salinity >= 25 ) {
            input.style.backgroundColor = "#9AC93D"
            input.style.color = "#000000"
        } else if ( salinity >= 20 ) {
            input.style.backgroundColor = "#FAFA3B"
            input.style.color = "#000000"
        } else if ( salinity >= 15 ) {
            input.style.backgroundColor = "#FFA30E"
            input.style.color = "#000000"
        } else if ( salinity >= 10 ) {
            input.style.backgroundColor = "#FF0000"
            input.style.color = "#FFFFFF"
        } else if ( salinity >= 5 ) {
            input.style.backgroundColor = "#840000"
            input.style.color = "#FFFFFF"
        } else {
            input.style.backgroundColor = "#000000"
            input.style.color = "#FFFFFF"
        }
     }
     
function init() {

   var str = document.getElementById("tide-now").content
   tide(str, "current-tide")

   var str = document.getElementById("tide-extreme-1").content
   tide(str, "next-tide-value-1")

   var str = document.getElementById("tide-extreme-2").content
   tide(str, "next-tide-value-2")

   var str = document.getElementById("tidal-status").content
   if ( str == "flood" ) {
	document.getElementById("galway-tidal-status").src="../../static/rising.png"
	document.getElementById("galway-tidal-status-label").innerText='RISING TIDE'
   } else if ( str == "ebb") {
	document.getElementById("galway-tidal-status").src="../../static/falling.png"
	document.getElementById("galway-tidal-status-label").innerText='FALLING TIDE'
   }
   document.getElementById("galway-tidal-status-label").style.fontWeight = "bold"

   var str = document.getElementById("surface-temperature-now").content
   temperature(str, "current-surface-temperature")

   var str = document.getElementById("minimum-surface-temperature-forecast").content
   temperature(str, "min-surface-temperature-forecast")

   var str = document.getElementById("maximum-surface-temperature-forecast").content
   temperature(str, "max-surface-temperature-forecast")

   var str = document.getElementById("surface-salinity-now").content
   salinity(str, "current-surface-salinity")

   var str = document.getElementById("minimum-surface-salinity-forecast").content
   salinity(str, "min-surface-salinity-forecast")

   var str = document.getElementById("maximum-surface-salinity-forecast").content
   salinity(str, "max-surface-salinity-forecast")
}
