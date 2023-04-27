export function addColumnFilters(table) {
  if (table.data().length === 1) {
    return;
  }
  table.columns().every(function() {
    var column = this;
    var header = $(column.header());
    var uniqueValues = column.data().unique().sort();

    if (header.text().indexOf("Referenced") != -1 || header.text() === "") {
      return;
    }

    // In some cases use dropdown filter
    if (header.text() == 'Type' ||
        (uniqueValues.length <= 20 && header.text() != "Tags")) {
      var select = $("<select>").appendTo(header).addClass("form-control")
        .addClass("filter")
        .attr("data-placeholder", "Filter " + header.text() + "...")
        .append($("<option>").val("").text(""));

      $.each(uniqueValues, function(index, value) {
        select.append($("<option>").val(value).text(value));
      });

      // Apply filter on select change
      select.on("change", function() {
        var value = $(this).val();
        if (value === "") {
          column.search("").draw();
        } else {
          column.search("^" + value + "$", true, false).draw();
        }
      });
    } else { // Otherwise, use text input filter
      var input = $("<input>").appendTo(header).addClass("form-control")
        .addClass("filter")
        .attr("placeholder", "Filter " + header.text() + "...");

      // Apply filter on input change
      input.on("keyup", function() {
        var value = $(this).val().toLowerCase();
        column.search(value, false, true).draw();
      });
    }
  });
}
