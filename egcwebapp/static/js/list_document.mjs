import { initDocumentInfoTooltip } from "./document_info.mjs";

export function initTooltips() {
  $(".document-info").each(function() {
    const $pmidCell = $(this).prev();
    const pmid = $pmidCell.text();
    const url = $pmidCell.parent().next().find("a").attr("href");
    initDocumentInfoTooltip($(this), pmid, url);
  });
}

$(document).ready(function() {
  // Initialize DataTables
  $("#document-table").DataTable( {
    "drawCallback": function( settings ) {
      initTooltips();
    }
  });
});