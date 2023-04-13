import { initTooltip } from "./tooltips.js";
import { initRelatedTooltips } from "./tooltips.js";

export async function initTooltips() {
    initRelatedTooltips(".extract-info", "extracts");
    initRelatedTooltips(".attribute-info", "attributes");
    initRelatedTooltips(".group-info", "groups");
}

$(document).ready(function() {
  // Initialize DataTables
  $("#crule-table").DataTable( {
    "drawCallback": function( settings ) {
      initTooltips();
    }
  });
});

