import { initRelatedTooltips } from "./tooltips.js";

export async function initTooltips() {
  initRelatedTooltips(".group-info", "groups");
}

$(document).ready(function() {
  // Initialize DataTables
  $("#group-table").DataTable( {
    "drawCallback": function( settings ) {
      initTooltips();
    }
  });
});

