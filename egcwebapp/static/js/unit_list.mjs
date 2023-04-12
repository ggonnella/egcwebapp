import { initTooltip } from "./tooltips.js";

$(document).ready(function() {
  // Initialize DataTables
  $("#unit-table").DataTable( {
    "drawCallback": function( settings ) {
      initTooltips();
    }
  });
});

