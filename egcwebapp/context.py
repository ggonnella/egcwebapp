import urllib.parse
import re
from pathlib import Path
from flask import render_template, current_app
from egcwebapp.formatting import break_string
from egcwebapp.external_links import link_external_resource, \
                                     link_uniprotkb_query


def common_context_processors():

    def column_template(record_kind, column):
      record_kind_specific = "columns/" + record_kind + "_" + column + ".html"
      generic = "columns/record_" + column + ".html"
      templatesdir = Path(current_app.root_path) / 'templates'
      if (templatesdir / record_kind_specific).exists():
        return record_kind_specific
      elif (templatesdir / generic).exists():
        return generic
      else:
        return None

    def tooltip_js(record_kind):
      record_kind_specific = f"js/{record_kind}_tooltips.mjs"
      staticdir = Path(current_app.root_path) / "static"
      if (staticdir / record_kind_specific).exists():
        return record_kind_specific
      else:
        return None

    return {
            'column_template': column_template,
            'tooltip_js': tooltip_js
           }

def column_context_processors():

    def linked_tag_value(tag_type, tag_value):
      if tag_type in ["XD", "XR"]:
        linked = []
        for value_part in tag_value.split(";"):
          m = re.match(r"^(.+):([^!#]+)([!#].*)?$", value_part)
          link = None
          if m:
            resource = m.group(1)
            item = m.group(2)
            link = link_external_resource(resource, item, value_part)
          if link:
            linked.append(link)
          else:
            linked.append(value_part)
        return ";".join(linked)
      else:
        return tag_value

    def model_model_id(record):
      link = link_external_resource(record['resource_id'], record['model_id'])
      if link:
        return link
      else:
        return record['model_id']

    def unit_symbol(record):
      if record['type']["base_type"] in ["specific_gene", "specific_protein",
                                         "function", "protein_complex"]:
        if record['symbol'] == ".":
          return record['symbol']
        symq = urllib.parse.quote(record['symbol'], safe='')
        query= f"query=(gene:{symq})%20OR%20(protein_name:{symq})"
        return record['symbol'] + " " + link_uniprotkb_query(query)
      else:
        return record['symbol']

    def unit_description(record):
      unit_type = record['type']['base_type']
      description = record['description']
      if unit_type in ["specific_gene", "specific_protein",
                       "function", "protein_complex"]:
        if description == ".":
          return description
        desq = description.replace("[", "(").replace("]", ")")
        desq = urllib.parse.quote(desq, safe='')
        return description + " " + link_uniprotkb_query(desq)
      else:
        return description

    def group_definition(record, in_tooltip, ancestor_ids):
        group_id = record['id']
        group_type = record['type']
        definition = record['definition']
        m = re.match(r"^(.+):([^!#]+)([!#].*)?$", definition)
        if m:
          definition_prefix = m.group(1)
          definition_id = m.group(2)
          link = link_external_resource(definition_prefix,
                                        definition_id,
                                        definition)
          if link:
            return link
        rel_groups = []
        definition_pieces = break_string(definition, 12, 8)
        output = []
        for definition in definition_pieces:
          if group_type == 'combined' or group_type == 'inverted':
              rel_groups = re.findall(r"[a-zA-Z0-9_]+", definition)
          else:
              m = re.match(r'^derived:([a-zA-Z0-9_]+):.*', definition)
              if m:
                  rel_groups = [m.group(1)]

          for rel_group in rel_groups:
              rendered_template = render_template('refs_link.html',
                  in_tooltip=in_tooltip,
                  record_kind='group', record_id=group_id,
                  related_kind='group', related_id=rel_group,
                  ancestor_ids=ancestor_ids, prev='list_group',
                  egc_data=current_app.egc_data)
              definition = re.sub(r'\b' + re.escape(rel_group) + r'\b',
                  rendered_template, definition)
          definition = '<span class="related_link">' +\
                            definition + '</span>'
          output.append(definition)

        return "<br/>".join(output)

    def unit_definition(record, in_tooltip, ancestor_ids):
        unit_id = record['id']
        base_type = record['type']['base_type']
        kind = record['type']['kind']
        resource = record['type'].get('resource', None)
        enumerating = record['type']['enumerating']
        multi = record['type']['multi']
        definition = record['definition']
        if definition == ".":
          return definition
        if kind == "category":
          if base_type in ['family_or_domain', 'function', 'ortholog_group',
                           'ortholog_group_category']:
            if resource in ['InterPro', 'Pfam', 'TC', 'Pfam_clan', 'CDD',
                            'EC', 'BRENDA_EC', 'GO', 'COG', 'COG_category',
                            'arCOG']:
              return link_external_resource(resource, definition)
        elif not enumerating:
          if base_type in ['feature_type', 'amino_acid'] \
              and definition.startswith('SO:'):
            return link_external_resource('SO', definition[3:], definition)
          elif base_type == 'metabolic_pathway' \
              and definition.startswith('KEGG:'):
            return link_external_resource('KEGG', definition[5:], definition)
        m = re.match(r"^ref:(.+):(.*)$", definition)
        if m:
          return "ref:" + link_external_resource(m.group(1), m.group(2),
              definition[4:])
        if not enumerating and multi:
          definition_parts = definition.split(",")
          output_parts = [unit_definition({'id': unit_id,
              'type': {"base_type": base_type, "multi": False,
                       "kind": "simple", "enumerating": False},
              "definition": part}, in_tooltip, ancestor_ids) \
                  for part in definition_parts]
          return ",".join(output_parts)
        definition_pieces = break_string(definition, 15)
        output = []
        for definition in definition_pieces:
          rel_units = []
          if base_type.startswith('homolog_'):
              m = re.match(r'^homolog:([a-zA-Z0-9_]+)', definition)
              if m:
                  rel_units = [m.group(1)]
          elif base_type == 'arrangement' and enumerating:
              parts = definition.split(',')
              rel_units = []
              for part in parts:
                  m = re.match(r'^([a-zA-Z0-9_]+)$', part)
                  if m:
                      rel_units.append(m.group(1))
          elif enumerating:
            rel_units = re.findall(r"[a-zA-Z0-9_]+", definition)
          elif definition.startswith('derived:'):
              m = re.match(r'^derived:([a-zA-Z0-9_]+):.*', definition)
              if m:
                rel_units = [m.group(1)]

          for rel_unit in rel_units:
              rendered_template = render_template('refs_link.html',
                  in_tooltip=in_tooltip,
                  record_kind='unit', record_id=unit_id,
                  related_kind='unit', related_id=rel_unit, prev='list_unit',
                  noclass=True, ancestor_ids=ancestor_ids,
                  egc_data=current_app.egc_data)
              definition = re.sub(r'\b' + re.escape(rel_unit) + r'\b',
                  rendered_template, definition)
          definition = '<span class="related_link">' +\
                            definition + '</span>'
          output.append(definition)

        return "<br/>".join(output)

    return {
            'linked_tag_value': linked_tag_value,
            'group_definition': group_definition,
            'unit_definition': unit_definition,
            'model_model_id': model_model_id,
            'unit_symbol': unit_symbol,
            'unit_description': unit_description,
           }
