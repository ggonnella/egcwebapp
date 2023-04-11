import { initTooltip } from "./document_info.js";

$(document).ready(function() {
  // Initialize DataTables
  $("#attribute-table").DataTable( {
    "drawCallback": function( settings ) {
      initTooltips();
    }
  });
});

