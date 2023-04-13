export function createSubItemsEventListener(thisRecordsName, nestedRecordsName,
                                     colspan) {
  return function(event) {
    event.preventDefault();
    var $count = $(this).closest(`.${nestedRecordsName}-count`);
    var recordId = $count.data('record-id');
    var $currentRow = $count.closest('tr');

    $.ajax({
      url: `/api/${thisRecordsName}/${recordId}/${nestedRecordsName}`,
      type: 'GET',
      success: function(response) {
        console.log(`Success fetching ${nestedRecordsName}`);

        const nestedClassName = `nested-${nestedRecordsName}`;
        // Remove existing nested table if any
        if ($currentRow.next(`.${nestedClassName}`).length > 0) {
          $currentRow.next(`.${nestedClassName}`).remove();
        }

        // Create a new row below the current row
        // Create a new cell that spans all the columns in the table
        var $newRow = $(`<tr class="${nestedClassName}"></tr>`);
        var $newCell = $(`<td colspan="${colspan}"></td>`);

        // Append the response to the new cell
        // Append the new cell to the new row
        // Insert the new row below the current row
        $newCell.append(response);
        $newRow.append($newCell);
        $currentRow.after($newRow);
      },
      error: function(response) {
        console.log(`Error fetching ${nestedRecordsName}:`, response);
      }
    });
  }
}
