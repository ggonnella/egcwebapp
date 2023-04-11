import { initTooltip } from "./document_info.js";

$(document).ready(function() {
  // Initialize DataTables
  $("#unit-table").DataTable( {
    "drawCallback": function( settings ) {
      initTooltips();
    }
  });
});

