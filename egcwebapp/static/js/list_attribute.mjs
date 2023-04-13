import { initTooltip } from "./tooltips.js";
import { initRelatedTooltips } from "./tooltips.js";

export async function initTooltips() {
  initRelatedTooltips(".unit-info", "units");
}

$(document).ready(function() {
  // Initialize DataTables
  $("#attribute-table").DataTable( {
    "drawCallback": function( settings ) {
      initTooltips();
    }
  });
});

