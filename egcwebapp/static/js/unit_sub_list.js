$(function() {
$('body').on('click', '.show-units', function(event) {
event.preventDefault();
var $unitsCount = $(this).closest('.units-count');
var attributeId = $unitsCount.data('attribute-id');
var $currentRow = $unitsCount.closest('tr');

$.ajax({
  url: '/api/attributes/' + attributeId + "/units",
  type: 'GET',
  success: function(response) {
    console.log('Success fetching units');

    // Remove existing nested table if any
    if ($currentRow.next('.nested-units').length > 0) {
      $currentRow.next('.nested-units').remove();
    }

    // Create a new row below the current row
    var $newRow = $('<tr class="nested-units"></tr>');

    // Create a new cell that spans all the columns in the table
    var $newCell = $('<td colpan="3"></td>');

    // Append the response to the new cell
    $newCell.append(response);

    // Append the new cell to the new row
    $newRow.append($newCell);

    // Insert the new row below the current row
    $currentRow.after($newRow);
  },
  error: function(response) {
    console.log('Error fetching units:', response);
  }
});
});
});s