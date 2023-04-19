export function openNestedTable(thisRecordsName, nestedRecordsName, colspan) {
  return function(event) {
    event.preventDefault();
    var $count = $(this).closest(`.count-${thisRecordsName}-${nestedRecordsName}`);
    var ancestorIds = $count.data('ancestor-ids');
    var $currentRow = $count.closest('tr');

    $.ajax({
      url: `/api/${thisRecordsName}/${ancestorIds}/${nestedRecordsName}`,
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

export function initNestedTable(table_id) {
  var table = $('#' + table_id).DataTable();
  addCloseButton(table_id);
  return table;
}

export function openRelatedNested(thisRecordsName, nestedRecordsName, colspan) {
  return function(event) {
    event.preventDefault();
    var $link = $(this).closest(`.related-${thisRecordsName}-${nestedRecordsName}`);
    var relatedId = $link.data('related-id');
    var ancestorIds = $link.data('ancestor-ids');
    var $currentRow = $link.closest('tr');

    $.ajax({
      url: `/api/ref/${ancestorIds}/${nestedRecordsName}/${relatedId}`,
      type: 'GET',
      success: function(response) {
        console.log(`Success fetching ${nestedRecordsName} ${relatedId}`);

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
        console.log(`Error fetching ${nestedRecordsName} ${relatedId}:`,
          response);
      }
    });
  }
}


function addCloseButton(table_id) {
  const buttonId = `close-nested-table-${table_id}`;
  const $button = $(`#${buttonId}`);
  if ($button.length == 0) {
    var closeButton = $(`<button id="${buttonId}" class="btn btn-sm btn-light" style="margin-left: 10px;"><i class="fas fa-times"></i></button>`);
    closeButton.on('click', closeNestedTable);
    $(`#${table_id}-wrapper .dataTables_filter`).append(closeButton);
  }
}

function closeNestedTable() {
  var $nestedTable = $(this).closest('div.dataTables_wrapper').parent().parent().parent();
  if ($nestedTable.length > 0) {
    $nestedTable.remove();
  }
}
