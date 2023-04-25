import { initTooltip } from "./tooltips.js";
import { initRelatedTooltips } from "./tooltips.js";
import { addColumnFilters } from "./datatable_filters.mjs";

export async function initTooltips() {
  initRelatedTooltips(".unit-info", "units");
}

$(document).ready(function() {
  var table = $("#attribute-table").DataTable( {
    "drawCallback": function( settings ) {
      initTooltips();
    }
  });
  addColumnFilters(table);
});

