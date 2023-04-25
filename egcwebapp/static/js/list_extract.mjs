import { initTooltip } from "./tooltips.js";
import { initRelatedTooltips } from "./tooltips.js";
import { addColumnFilters } from "./datatable_filters.mjs";

export async function initTooltips() {
  initRelatedTooltips(".document-info", "documents");
}

$(document).ready(function() {
  var table = $("#extract-table").DataTable( {
    "drawCallback": function( settings ) {
      initTooltips();
    }
  });
  addColumnFilters(table);
});

