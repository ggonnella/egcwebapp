$(function() {
  $('body').on('click', '.show-extracts', function(event) {
    event.preventDefault();
    var $extractsCount = $(this).closest('.extracts-count');
    var documentId = $extractsCount.data('document-id');
    var $currentRow = $extractsCount.closest('tr');

    $.ajax({
      url: '/api/documents/' + documentId + "/extracts",
      type: 'GET',
      success: function(response) {
        console.log('Success fetching extract');

        // Remove existing nested table if any
        if ($currentRow.next('.nested-extracts').length > 0) {
          $currentRow.next('.nested-extracts').remove();
        }

        // Create a new row below the current row
        var $newRow = $('<tr class="nested-extracts"></tr>');

        // Create a new cell that spans all the columns in the table
        var $newCell = $('<td colspan="4"></td>');

        // Append the response to the new cell
        $newCell.append(response);

        // Append the new cell to the new row
        $newRow.append($newCell);

        // Insert the new row below the current row
        $currentRow.after($newRow);
      },
      error: function(response) {
        console.log('Error fetching extracts:', response);
      }
    });
  });
});

