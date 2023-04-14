import { initRelatedTooltips } from "./tooltips.js";

export async function initTooltips() {
  initRelatedTooltips(".unit-info", "units");
}

$(document).ready(function() {
  // Initialize DataTables
  $("#unit-table").DataTable( {
    "drawCallback": function( settings ) {
      initTooltips();
    }
  });
});

