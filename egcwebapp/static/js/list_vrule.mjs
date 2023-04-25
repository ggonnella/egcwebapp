import { initTooltip } from "./tooltips.js";
import { initRelatedTooltips } from "./tooltips.js";
import { addColumnFilters } from "./datatable_filters.mjs";

export async function initTooltips() {
    initRelatedTooltips(".extract-info", "extracts");
    initRelatedTooltips(".attribute-info", "attributes");
    initRelatedTooltips(".group-info", "groups");
}

$(document).ready(function() {
  var table = $("#vrule-table").DataTable( {
    "drawCallback": function( settings ) {
      initTooltips();
    }
  });
  addColumnFilters(table);
});

