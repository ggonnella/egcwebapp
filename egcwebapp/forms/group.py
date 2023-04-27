from wtforms import Form, StringField, validators, \
                    FieldList, FormField, BooleanField
import re
from .tag import TagForm

class GroupForm(Form):
  id = StringField('Group ID', [validators.Regexp('[a-zA-Z0-9_]+'),
    validators.DataRequired()])
  auto_id = BooleanField('Auto-generate ID', default=False)
  name = StringField('Group Name', [validators.Length(min=1, max=50),
    validators.DataRequired()])
  type = StringField('Group Type', [validators.Length(min=1, max=50),
    validators.DataRequired()])
  definition = StringField('Group Definition', [validators.Length(min=1),
    validators.DataRequired()])
  tags = FieldList(FormField(TagForm), min_entries=1, label="Tags")
  comment = StringField('Comment')

  def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)
      self.egc_data = kwargs.pop('egc_data')
      self.old_id = kwargs.pop('old_id', None)
      self.script = TagForm.Script
      if self.auto_id.data:
        self.id.render_kw = {'readonly': True}
        self.id.data = 'auto_generated'

  @classmethod
  def from_record(cls, form, record, **kwargs):
    form_data = {
        "id": record["id"],
        "name": record["name"],
        "type": record["type"],
        "definition": record["definition"],
    }
    TagForm.add_tags_to_form_data(record, form_data)
    kwargs["data"] = form_data
    return cls(form, **kwargs)

  def validate_id(self, field):
    if self.auto_id.data:
      return True
    new_id = field.data
    if self.old_id != new_id:
      if self.egc_data.id_exists(new_id):
        raise validators.ValidationError('Record ID already exists')

  TypePfx = {
        "requirement": "r",
        "specific_nutrient_availablity": "r",
        "biological_interaction": "i",
        "biological_interaction_partner_taxonomy": "ip",
        "combined": "c",
        "cultiviability": "cv",
        "geographical": "g",
        "gram_stain": "gs",
        "habitat": "h",
        "inverted": "n",
        "metabolic": "m",
        "metagenome_assembled": "ma",
        "paraphyletic": "pt",
        "resultive_disease_symptom": "d",
        "strain": "s",
        "taxis": "x",
        "taxonomic": "t",
        "trophic_strategy": "ts",
        None: "x",
      }

  def auto_generate_id(self):
    if self.auto_id.data:
      name = self.name.data.split(" ")
      name = [re.sub(r"[^a-zA-Z0-9_]", "", n) for n in name]
      name = "_".join([n[:5] for n in name if n])
      gtype = self.type.data
      if gtype.endswith("_requirement"):
        pfx = self.TypePfx["requirement"]
      else:
        pfx = self.TypePfx.get(gtype, self.TypePfx[None]+gtype[0])

      self.id.data = f'G{pfx}_{name}'
      if self.id.data == self.old_id:
        return
      if self.egc_data.id_exists(self.id.data):
        sfx = 2
        while True:
          sfx_id = f'{self.id.data}_{sfx}'
          if sfx_id == self.old_id or not self.egc_data.id_exists(sfx_id):
            self.id.data = sfx_id
            break
          sfx += 1

  def validate_tags(self, field):
    TagForm.tags_validator(field)

  def to_record(form):
    record_data = {
        "record_type": "G",
        "id": form.id.data,
        "name": form.name.data,
        "type": form.type.data,
        "definition": form.definition.data,
    }
    TagForm.add_tags_from_form(form, record_data)
    return record_data
