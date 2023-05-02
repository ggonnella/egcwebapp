from wtforms import Form, StringField, validators, \
                    FieldList, FormField, BooleanField, SelectField
from jinja2 import Markup
from .tag import TagForm
from egctools import id_generator

class GroupForm(Form):
  id = StringField('Group ID', [validators.Regexp('[a-zA-Z0-9_]+'),
    validators.DataRequired()])
  auto_id = BooleanField('Auto-generate ID', default=False)
  name = StringField('Group Name', [validators.Length(min=1, max=50),
    validators.DataRequired()])
  type = SelectField('Group Type', [validators.DataRequired()],
      choices=[], coerce=str)
  custom_type = StringField('Custom Group Type')
  definition = StringField('Group Definition', [validators.Length(min=1),
    validators.DataRequired()])
  tags = FieldList(FormField(TagForm), min_entries=1, label="Tags")
  comment = StringField('Comment')

  Script = Markup('''
    $(document).ready(function () {
      const $typeSelect = $(".type-field");
      const $customTypeInput = $(".custom_type-field");
      function updateCustomTypeState() {
        if ($typeSelect.val() === "custom") {
          $customTypeInput.prop("disabled", false);
          $customTypeInput.prop("required", true);
        } else {
          $customTypeInput.prop("disabled", true);
          $customTypeInput.prop("required", false);
        }
      }
      $typeSelect.on("change", updateCustomTypeState);
      updateCustomTypeState();
    });
  ''')

  def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)
      self.egc_data = kwargs.pop('egc_data')
      self.old_id = kwargs.pop('old_id', None)
      self.script = GroupForm.Script
      self.script += TagForm.Script
      if self.auto_id.data:
        self.id.render_kw = {'readonly': True}
        self.id.data = 'auto_generated'
      self.type.choices = self.egc_data.pgto_choices() +\
                          [("custom", "Custom Group Type")]

  @classmethod
  def from_record(cls, form, record, **kwargs):
    form_data = {
        "id": record["id"],
        "name": record["name"],
        "type": record["type"],
        "definition": record["definition"],
    }
    if form_data["type"] not in kwargs['egc_data'].pgto_types():
        form_data["custom_type"] = form_data["type"]
        form_data["type"] = "custom"
    TagForm.add_tags_to_form_data(record, form_data)
    kwargs["data"] = form_data
    return cls(form, **kwargs)

  def validate_definition(self, field):
    if self.type.data == "combined" or \
        self.type.data == "inverted":
      try:
        group_names = self.egc_data.get_lexpr_ids(field.data)
        for name in group_names:
          if not self.egc_data.id_exists(name):
            raise validators.ValidationError(
                "Group '{}' does not exist".format(name))
      except Exception as e:
        raise validators.ValidationError(str(e))
    return True

  def validate_id(self, field):
    if self.auto_id.data:
      return True
    new_id = field.data
    if self.old_id != new_id:
      if self.egc_data.id_exists(new_id):
        raise validators.ValidationError('Record ID already exists')

  def auto_generate_id(self):
    if self.auto_id.data:
      self.id.data = id_generator.generate_G_id(\
          self.egc_data, self.name.data, self.type.data, self.old_id)

  def validate_tags(self, field):
    TagForm.tags_validator(field)

  def validate_type(self, field):
      if field.data == "custom" and not self.custom_type.data:
          raise validators.ValidationError("Please enter a custom group type")

  def to_record(form):
    record_data = {
        "record_type": "G",
        "id": form.id.data,
        "name": form.name.data,
        "type": form.type.data,
        "definition": form.definition.data,
    }
    if form.type.data == "custom":
        record_data["type"] = form.custom_type.data
    TagForm.add_tags_from_form(form, record_data)
    return record_data
