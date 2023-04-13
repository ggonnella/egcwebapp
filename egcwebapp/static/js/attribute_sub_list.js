$(function() {
  $('body').on('click', '.show-attributes', function(event) {
    event.preventDefault();
    var $count = $(this).closest('.attributes-count');
    var recordId = $count.data('record-id');
    var $currentRow = $count.closest('tr');

    $.ajax({
      url: '/api/units/' + recordId + "/attributes",
      type: 'GET',
      success: function(response) {
        console.log('Success fetching attributes');

        // Remove existing nested table if any
        if ($currentRow.next('.nested-attributes').length > 0) {
          $currentRow.next('.nested-attributes').remove();
        }

        // Create a new row below the current row
        var $newRow = $('<tr class="nested-attributes"></tr>');

        // Create a new cell that spans all the columns in the table
        var $newCell = $('<td colspan="8"></td>');

        // Append the response to the new cell
        $newCell.append(response);

        // Append the new cell to the new row
        $newRow.append($newCell);

        // Insert the new row below the current row
        $currentRow.after($newRow);
      },
      error: function(response) {
        console.log('Error fetching attributes:', response);
      }
    });
  });
});

