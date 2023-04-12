import { initTooltip } from "./tooltips.js";

$(document).ready(function() {
  // Initialize DataTables
  $("#attribute-table").DataTable( {
    "drawCallback": function( settings ) {
      initTooltips();
    }
  });
});

