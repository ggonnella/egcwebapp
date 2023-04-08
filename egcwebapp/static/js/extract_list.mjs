import { initTooltip } from "./document_info.js";

$(document).ready(function() {
  // Initialize DataTables
  $("#extract-table").DataTable( {
    "drawCallback": function( settings ) {
      initTooltips();
    }
  });
  async function initTooltips() {
    $(".document-info").each(function() {
      const documentId = $(this).prev().text();
      const response = fetch(`/api/documents/${documentId}`);
      if (!response.ok) {
        console.error("Failed to fetch D record information for document " + documentId);
        content += "<p>Error: Failed to fetch D record information for document " + documentId + "</p>";
      } else {
        const document = response.json();
        content += `<p>D record:</p><pre>${document.text}</pre>`;
      }
      initTooltip($(this), "D record", content);
    });
  }
});
