export function activateAutoIdCheckboxes() {
  const $autoIdCheckboxes = $('.auto_id-checkbox');
  if ($autoIdCheckboxes.length > 0) {
    $autoIdCheckboxes.each(function() {
      $(this).off('change');
      $(this).on('change', toggleAutoId);
    });
  }
}

function toggleAutoId(event) {
  const autoIdCheckbox = $(event.target);
  const divWrapper = autoIdCheckbox.parent();
  const idInput = divWrapper.find('.id_field');
  if (autoIdCheckbox.prop('checked')) {
    idInput.prop('readonly', true);
  } else {
    idInput.prop('readonly', false);
  }
}
