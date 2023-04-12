import { initTooltip } from "./tooltips.js";
import { initRelatedTooltips } from "./tooltips.js";

$(document).ready(function() {
  // Initialize DataTables
  $("#attribute-table").DataTable( {
    "drawCallback": function( settings ) {
      initTooltips();
    }
  });
  async function initTooltips() {
    initRelatedTooltips(".unit-info", "units");
  }
});

