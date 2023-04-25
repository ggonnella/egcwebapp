import { addColumnFilters } from './datatable_filters.mjs';

export function openNestedTable(thisRecordsName, nestedRecordsName, colspan) {
  return function(event) {
    event.preventDefault();
    var $count = $(this).closest(`.count-${thisRecordsName}-${nestedRecordsName}`);
    var ancestorIds = $count.data('ancestor-ids');
    var $currentRow = $count.closest('tr');
    const msg = `${nestedRecordsName} which refer to ${ancestorIds}`;

    $.ajax({
      url: `/api/${thisRecordsName}/${ancestorIds}/${nestedRecordsName}`,
      type: 'GET',
      success: function(response) {
        console.log(`Success fetching ${msg}`);

        const nestedClassName = `nested-${nestedRecordsName}`;
        // Remove existing nested table if any
        if ($currentRow.next(`.${nestedClassName}`).length > 0) {
          $currentRow.next(`.${nestedClassName}`).remove();
        }

        var $newRow = $(`<tr class="${nestedClassName}"></tr>`);
        var $newCell = $(`<td colspan="${colspan}"></td>`);

        $newCell.append(response);
        $newRow.append($newCell);
        $currentRow.after($newRow);
      },
      error: function(response) {
        console.log(`Error fetching ${msg}:`, response);
      }
    });
  }
}

export function openEditForm(event) {
  event.preventDefault();
  const recordId = $(this).data('record-id');
  const recordKind = $(this).data('record-kind');
  const colspan = $(this).data('colspan');
  const $currentRow = $(this).closest('tr');

  $.ajax({
    url: `/api/${recordKind}s/${recordId}/edit`,
    type: 'GET',
    success: function(response) {

      const nestedClassName = `nested-edit-form`;
      // Remove existing nested form if any
      if ($currentRow.next(`.${nestedClassName}`).length > 0) {
        $currentRow.next(`.${nestedClassName}`).remove();
      }

      const $newRow = $(`<tr class="${nestedClassName}"></tr>`);
      const $newCell = $(`<td colspan="${colspan}"></td>`);

      $newCell.append(response);
      $newRow.append($newCell);
      $currentRow.after($newRow);
    },
    error: function(response) {
      console.log(`Error fetching edit form for ${recordKind} ${recordId}:`,
        response);
    }
  });
}

export function submitNestedEditForm(event) {
  event.preventDefault();

  const $form = $(this);
  const recordKind = $form.data('record-kind');
  const recordId = $form.data('record-id');

  const formData = new FormData($form[0]);

  $.ajax({
    url: `/api/${recordKind}s/${recordId}/update`,
    type: 'POST',
    data: formData,
    contentType: false,
    processData: false,
    success: function(response) {
      const $currentRow = $form.closest('tr');
      // response is a JSON dictionary with the following keys:
      // - success: boolean
      // - html: string
      if (response.success) {
        console.log(`Success updating ${recordKind} ${recordId}`);
        $currentRow.prev().replaceWith(response.html);
        $currentRow.remove();
      } else {
        console.log(`Failure updating ${recordKind} ${recordId}`);
        const colspan = $currentRow.children('td').attr('colspan');
        const $newRow = $(`<tr class="nested-edit-form"></tr>`);
        const $newCell = $(`<td colspan="${colspan}"></td>`);
        $newCell.append(response.html);
        $newRow.append($newCell);
        $currentRow.replaceWith($newRow);
      }
    },
    error: function(response) {
    }
  });
}

export function initNestedTable(table_id, drawCallback) {
  var table = $('#' + table_id).DataTable({
    "drawCallback": drawCallback
  });
  addCloseButton(table_id);
  return table;
}

export function initMainTable(table_id, drawCallback) {
  var table = $('#' + table_id).DataTable({
    "drawCallback": drawCallback
  });
  addColumnFilters(table);
  return table;
}

export function openRelatedNested(thisRecordsName, nestedRecordsName, colspan) {
  return function(event) {
    event.preventDefault();
    var $link = $(this).closest(`.related-${thisRecordsName}-${nestedRecordsName}`);
    var relatedId = $link.data('related-id');
    var ancestorIds = $link.data('ancestor-ids');
    var $currentRow = $link.closest('tr');
    const msg = `${nestedRecordsName} '${relatedId}' related to: ${ancestorIds}`;

    $.ajax({
      url: `/api/ref/${ancestorIds}/${nestedRecordsName}/${relatedId}`,
      type: 'GET',
      success: function(response) {
        console.log(`Success fetching ${msg}`);

        const nestedClassName = `nested-${nestedRecordsName}`;
        // Remove existing nested table if any
        if ($currentRow.next(`.${nestedClassName}`).length > 0) {
          $currentRow.next(`.${nestedClassName}`).remove();
        }

        var $newRow = $(`<tr class="${nestedClassName}"></tr>`);
        var $newCell = $(`<td colspan="${colspan}"></td>`);
        $newCell.append(response);
        $newRow.append($newCell);
        $currentRow.after($newRow);
        console.log(`Done with ${msg}`);
      },
      error: function(response) {
        console.log(`Error fetching ${msg}:`, response);
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
    $(`#${table_id}_wrapper .dataTables_filter`).append(closeButton);
  }
}

function closeNestedTable() {
  var $nestedTable = $(this).closest('div.dataTables_wrapper').parent().parent();
  if ($nestedTable.length > 0) {
    $nestedTable.remove();
  }
}
