# Organization of the templates

list.html/record_form.html/show.html -> filename.html

list.html -> datatable.html -> row.html -> column.html -> columns/... -> ref_by_link.html
                                                                      -> refs_link.html
                                        -> actions_column.html
                            -> jslinks.html

show.html -> (same as list.html but for a single record)

nested tables routes -> datatable.html -> ... (same as in list.html but main = False)

tooltips in datatable -> table.html -> column.html -> columns/... (with in_tooltips = True)

/api/<record_id>/update -> row.html -> ... (same as in list.html)
                        -> jslinks.html

/api/<record_id>/edit|update -> nested_record_form.html -> form_fields.html -> field_error.html

/<record_id>/edit -> record_form.html -> form_fields.html -> field_error.html

