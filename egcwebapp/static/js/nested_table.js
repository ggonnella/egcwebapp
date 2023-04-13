export function initNestedTable(table_id) {
  var table = $('#' + table_id).DataTable();
  addCloseButton(table_id);
  return table;
}

function addCloseButton(table_id) {
  var closeButton = $('<button id="close-nested-table" class="btn btn-sm btn-light" style="margin-left: 10px;"><i class="fas fa-times"></i></button>');
  closeButton.on('click', closeNestedTable);
  $(`#${table_id}-wrapper .dataTables_filter`).append(closeButton);
}

function closeNestedTable() {
  var $nestedTable = $(this).closest('div.dataTables_wrapper').parent().parent().parent();
  if ($nestedTable.length > 0) {
    $nestedTable.remove();
  }
}
