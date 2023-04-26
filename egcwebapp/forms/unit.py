from wtforms import Form, StringField, validators, \
                    FieldList, FormField, BooleanField
import re
from .tag import TagForm

class UnitForm(Form):
  id = StringField('Record ID', [validators.Length(min=1, max=50),
                               validators.Regexp('[a-zA-Z0-9_]+'),
                               validators.DataRequired()])
  auto_id = BooleanField('Auto-generate ID', default=False)
  type = StringField('Type', validators=[validators.DataRequired()])
  definition = StringField('Definition', validators = [validators.DataRequired()])
  symbol = StringField('Symbol', validators=[validators.DataRequired()])
  description = StringField('Description', validators=[validators.DataRequired()])
  tags = FieldList(FormField(TagForm), min_entries=1, label="Tags")
  comment = StringField('Comment')

  def to_record(form):
    record_data = {
        "record_type": "U",
        "id": form.id.data,
        "type": form.type.data,
        "definition": form.definition.data,
        "symbol": form.symbol.data,
        "description": form.description.data
    }
    TagForm.add_tags_from_form(form, record_data)
    return record_data

  @classmethod
  def from_record(cls, form, record, **kwargs):
    form_data = {
        "id": record["id"],
        "type": record["type"],
        "definition": record["definition"],
        "symbol": record["symbol"],
        "description": record["description"]
    }
    TagForm.add_tags_to_form_data(record, form_data)
    kwargs["data"] = form_data
    return cls(form, **kwargs)

  def validate(self):
    if not super().validate():
      return False
    if all(x == "." for x in \
        [self.definition.data, self.symbol.data, self.description.data]):
      msg = 'At least one of definition, symbol, or description must be present'
      self.definition.errors.append(msg)
      self.symbol.errors.append(msg)
      self.description.errors.append(msg)
      return False
    return True

  def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)
      self.egc_data = kwargs.pop('egc_data')
      self.old_id = kwargs.pop('old_id', None)
      self.script = TagForm.Script
      if self.auto_id.data:
        self.id.render_kw = {'readonly': True}
        self.id.data = 'auto_generated'

  def validate_id(self, field):
    if self.auto_id.data:
      return True
    new_id = field.data
    if self.old_id != new_id:
      if not self.egc_data.is_unique_id(new_id):
          raise validators.ValidationError('Record ID already exists')

  TypePfx = {
        "amino_acid": "aa",
        "base": "b",
        "family_or_domain": "d",
        "feature_type": "t",
        "function": "f",
        "homolog_gene": "h",
        "homolog_protein": "h",
        "ortholog_group": "og",
        "ortholog_groups_category": "k",
        "protein_type": "pt",
        "protein_complex": "pc",
        "specific_gene": "g",
        "specific_protein": "p",
        "gene_cluster": "c",
        "gene_system": "y",
        "metabolic_pathway": "w",
        "genomic_island": "i",
        "trophic_strategy": "ts",
        "unit": "u",
        None: "x",
      }

  def auto_generate_id(self):
    if self.auto_id.data:
      utype = self.type.data
      if utype.startswith("*"):
        utype = utype[1:]
      m = re.match(r"set!?:\+?(.*)", utype)
      if m:
        utype = m.group(1)
      utype = utype.split(":")[0]
      pfx = self.TypePfx.get(utype, self.TypePfx[None]+utype[0])
      if self.symbol.data != ".":
        namesrc = [self.symbol.data]
      else:
        namesrc1 = self.definition.data.split(" ")
        namesrc2 = self.description.data.split(" ")
        if namesrc1 == ["."]:
          namesrc = namesrc2
        elif namesrc2 == ["."]:
          namesrc = namesrc1
        else:
          if len(namesrc2) == 1:
            namesrc = namesrc2
          elif len(namesrc1) == 1:
            namesrc = namesrc1
          else:
            namesrc = namesrc2
      namesrc = [re.sub(r"[^a-zA-Z0-9_]", "_", n) for n in namesrc]
      if len(namesrc) == 1:
        name = namesrc[0]
      else:
        name = "_".join([n[:5] for n in namesrc if n])

      self.id.data = f'U{pfx}_{name}'
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

