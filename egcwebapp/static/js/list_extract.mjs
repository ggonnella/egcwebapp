import { initTooltip } from "./tooltips.js";

export async function initTooltips() {
  $(".document-info").each(async function() {
    const documentId = $(this).prev().data('document-id');
    try {
      const response = await fetch(`/api/documents/${documentId}`);
      if (!response.ok) {
        console.error(`Failed to fetch D record information for document ${documentId}`);
        return "<p>Error: Failed to fetch D record information</p>";
      }
      const table = await response.text();
      const html = `<div class="tooltip-table">${table}</div>`
      initTooltip($(this), "D record", html);
    } catch (error) {
      console.error(`Failed to fetch D record information for document ${documentId}:`, error);
      return "<p>Error: Failed to fetch D record information</p>";
    }
  });
}

$(document).ready(function() {
  // Initialize DataTables
  $("#extract-table").DataTable( {
    "drawCallback": function( settings ) {
      initTooltips();
    }
  });
});

