import { initTooltip } from "./tooltips.js";
import { initRelatedTooltips } from "./tooltips.js";

export async function initTooltips() {
  initRelatedTooltips(".document-info", "documents");
}

$(document).ready(function() {
  // Initialize DataTables
  $("#extract-table").DataTable( {
    "drawCallback": function( settings ) {
      initTooltips();
    }
  });
});

