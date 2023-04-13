import { initTooltip } from "./tooltips.js";
import { initRelatedTooltips } from "./tooltips.js";

$(document).ready(function() {
  // Initialize DataTables
  $("#vrule-table").DataTable( {
    "drawCallback": function( settings ) {
      initTooltips();
    }
  });
  async function initTooltips() {
    initRelatedTooltips(".extract-info", "extracts");
    initRelatedTooltips(".attribute-info", "attributes");
    initRelatedTooltips(".group-info", "groups");
  }
});

