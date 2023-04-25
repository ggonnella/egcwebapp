import { initRelatedTooltips } from "./tooltips.js";
import { addColumnFilters } from "./datatable_filters.mjs";

export async function initTooltips() {
  initRelatedTooltips(".group-info", "groups");
}

$(document).ready(function() {
  var table = $("#group-table").DataTable( {
    "drawCallback": function( settings ) {
      initTooltips();
    }
  });
  addColumnFilters(table);
});

