import urllib.parse
import re
from flask import render_template, current_app
from egcwebapp.formatting import break_string

def processors():

    from egcwebapp.external_links import link_external_resource, \
                                         link_uniprotkb_query

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

    def linked_model_id(resource_id, model_id):
      link = link_external_resource(resource_id, model_id)
      if link:
        return link
      else:
        return model_id

    def linked_unit_symbol(unit_type, symbol):
      if unit_type in ["specific_gene", "specific_protein", "function",
      "set:protein_complex"]:
        if symbol == ".":
          return symbol
        symq = urllib.parse.quote(symbol, safe='')
        query= f"query=(gene:{symq})%20OR%20(protein_name:{symq})"
        return symbol + " " + link_uniprotkb_query(query)
      else:
        return symbol

    def linked_unit_description(unit_type, description):
      if unit_type in ["specific_gene", "specific_protein", "function",
      "set:protein_complex"]:
        if description == ".":
          return description
        desq = description.replace("[", "(").replace("]", ")")
        desq = urllib.parse.quote(desq, safe='')
        return description + " " + link_uniprotkb_query(desq)
      else:
        return description

    def linked_group_definition(group_id, group_type,
                                group_definition, ancestor_ids):
        m = re.match(r"^(.+):([^!#]+)([!#].*)?$", group_definition)
        if m:
          group_definition_prefix = m.group(1)
          group_definition_id = m.group(2)
          link = link_external_resource(group_definition_prefix,
                                        group_definition_id,
                                        group_definition)
          if link:
            return link
        rel_groups = []
        definition_pieces = break_string(group_definition, 12, 8)
        output = []
        for group_definition in definition_pieces:
          if group_type == 'combined' or group_type == 'inverted':
              rel_groups = re.findall(r"[a-zA-Z0-9_]+", group_definition)
          else:
              m = re.match(r'^derived:([a-zA-Z0-9_]+):.*', group_definition)
              if m:
                  rel_groups = [m.group(1)]

          for rel_group in rel_groups:
              rendered_template = render_template('refs_link.html',
                  record_kind='group', record_id=group_id,
                  related_kind='group', related_id=rel_group,
                  ancestor_ids=ancestor_ids, prev='list_group',
                  egc_data=current_app.egc_data)
              group_definition = re.sub(r'\b' + re.escape(rel_group) + r'\b',
                  rendered_template, group_definition)
          group_definition = '<span class="related_link">' +\
                            group_definition + '</span>'
          output.append(group_definition)

        return "<br/>".join(output)

    def linked_unit_definition(unit_id, unit_type,
                               unit_definition, ancestor_ids):
        if unit_definition == ".":
          return unit_definition
        if unit_type == 'family_or_domain:InterPro':
          return link_external_resource('InterPro', unit_definition)
        elif unit_type == 'family_or_domain:TC':
          return link_external_resource('TC', unit_definition)
        elif unit_type == 'family_or_domain:Pfam':
          return link_external_resource('Pfam', unit_definition)
        elif unit_type == 'family_or_domain:Pfam_clan':
          return link_external_resource('Pfam_clan', unit_definition)
        elif unit_type == 'family_or_domain:CDD':
          return link_external_resource('CDD', unit_definition)
        elif unit_type == 'function:EC':
          return link_external_resource('EC', unit_definition)
        elif unit_type == 'function:BRENDA_EC':
          return link_external_resource('BRENDA_EC', unit_definition)
        elif unit_type == 'function:GO':
          return link_external_resource('GO', unit_definition)
        elif unit_type == 'ortholog_groups_category:COG_category':
          return link_external_resource('COG_category', unit_definition)
        elif unit_type == 'ortholog_group:COG':
          return link_external_resource('COG', unit_definition)
        elif unit_type == 'ortholog_group:arCOG':
          return link_external_resource('arCOG', unit_definition)
        elif (unit_type == 'feature_type' or unit_type == 'amino_acid') and \
            unit_definition.startswith('SO:'):
          return link_external_resource('SO',
                unit_definition[3:], unit_definition)
        elif unit_type == 'set:metabolic_pathway' \
            and unit_definition.startswith('KEGG:'):
          return link_external_resource('KEGG',
                unit_definition[5:], unit_definition)
        m = re.match(r"^ref:(.+):(.*)$", unit_definition)
        if m:
          return "ref:" + link_external_resource(m.group(1), m.group(2),
              unit_definition[4:])
        if unit_type.startswith("set:+"):
          definition_parts = unit_definition.split(",")
          output_parts = [linked_unit_definition(unit_id, "set:" +\
              unit_type[5:], part, ancestor_ids) for part in definition_parts]
          return ",".join(output_parts)
        unit_definition_pieces = break_string(unit_definition, 15)
        output = []
        for unit_definition in unit_definition_pieces:
          rel_units = []
          if unit_type.startswith('homolog_'):
              m = re.match(r'^homolog:([a-zA-Z0-9_]+)', unit_definition)
              if m:
                  rel_units = [m.group(1)]
          elif unit_type == 'set!:arrangement':
              parts = unit_definition.split(',')
              rel_units = []
              for part in parts:
                  m = re.match(r'^([a-zA-Z0-9_]+)$', part)
                  if m:
                      rel_units.append(m.group(1))
          elif unit_type.startswith('*') or unit_type.startswith('set!:'):
              rel_units = re.findall(r"[a-zA-Z0-9_]+", unit_definition)
          elif unit_definition.startswith('derived:'):
              m = re.match(r'^derived:([a-zA-Z0-9_]+):.*', unit_definition)
              if m:
                rel_units = [m.group(1)]

          for rel_unit in rel_units:
              rendered_template = render_template('refs_link.html',
                  record_kind='unit', record_id=unit_id,
                  related_kind='unit', related_id=rel_unit, prev='list_unit',
                  noclass=True, ancestor_ids=ancestor_ids,
                  egc_data=current_app.egc_data)
              unit_definition = re.sub(r'\b' + re.escape(rel_unit) + r'\b',
                  rendered_template, unit_definition)
          unit_definition = '<span class="related_link">' +\
                            unit_definition + '</span>'
          output.append(unit_definition)

        return "<br/>".join(output)

    return {'linked_group_definition': linked_group_definition,
            'linked_unit_definition': linked_unit_definition,
            'linked_tag_value': linked_tag_value,
            'linked_model_id': linked_model_id,
            'linked_unit_symbol': linked_unit_symbol,
            'linked_unit_description': linked_unit_description,
           }
