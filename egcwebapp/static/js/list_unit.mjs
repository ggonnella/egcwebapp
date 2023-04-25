import { initRelatedTooltips } from "./tooltips.js";
import { addColumnFilters } from "./datatable_filters.mjs";

export async function initTooltips() {
  initRelatedTooltips(".unit-info", "units");
}

$(document).ready(function() {
  var table = $("#unit-table").DataTable( {
    "drawCallback": function( settings ) {
      initTooltips();
    }
  });
  addColumnFilters(table);
});

