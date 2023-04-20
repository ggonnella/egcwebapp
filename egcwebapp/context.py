import urllib.parse
import re
from flask import render_template, current_app

def break_string(string, goal_length, min_length=None, breaking_chars=" ,"):
    """Breaks a string into pieces of a desired length.

    The function tries to break the string into pieces of length
    `goal_length`, where the break can only happen at one of the
    characters contained in the string `breaking_chars`.

    If there is no such character at the desired breaking position,
    it can take one between the position `min_length` and the
    and `goal_length` of the remaining string.

    If also in that region there is none, then take the first available
    breaking point after position `goal_length` (or leave the remaining string
    unbroken if there are no further breaking characters).

    Args:
        string (str):                   The string to be broken into pieces.
        goal_length (int):              The desired length of the pieces.
        min_length (int):               The minimum length of the pieces.
                                        (default: 90% of `goal_length`)
        breaking_chars (str, optional): The characters at which the string
                                        can be broken (default: " ,").

    Returns:
        list: A list of the broken pieces of the original string.
              The breaking character is included in the piece before the break.

    Examples:
        >>> break_string("This is a very long string that needs a break.", 20)
        ['This is a very long ', 'string that needs a ', 'break.']

        >>> break_string("This is a test string", 10, breaking_chars="-")
        ['This is a test string']
    """
    # Check if string is already shorter than goal length
    if len(string) <= goal_length:
        return [string]

    if min_length is None:
      min_length = int(goal_length * 0.9)

    # Find the first breaking character at the goal length
    if string[goal_length] in breaking_chars:
        return [string[:goal_length+1]] + break_string(string[goal_length+1:],
                goal_length, min_length, breaking_chars)

    # Find the last breaking character before the deviation range
    last_break = -1
    for i in range(min_length, goal_length):
        if i >= 0 and string[i] in breaking_chars:
            last_break = i

    # Find the first breaking character after the goal length
    first_break = -1
    for i in range(goal_length+1, len(string)):
        if string[i] in breaking_chars:
            first_break = i
            break

    # Choose the preferred breaking position based on priority
    if last_break >= 0:
        return [string[:last_break+1]] + break_string(string[last_break+1:],
                goal_length, min_length, breaking_chars)
    elif first_break > 0:
        return [string[:first_break+1]] + break_string(string[first_break+1:],
                goal_length, min_length, breaking_chars)
    else:
        return [string]


def processors():

    DOI_URL = "https://doi.org/"
    GEONAMES_URL = "https://www.geonames.org/"
    OBO_URL = "http://purl.obolibrary.org/obo/"
    MICRO_URL = "https://www.ebi.ac.uk/ols4/ontologies/micro/classes/"+\
        "http%253A%252F%252Fpurl.obolibrary.org%252Fobo%252FMICRO_"
    WIKIPEDIA_URL = "https://en.wikipedia.org/wiki/"
    WIKTIONARY_URL = "https://en.wiktionary.org/wiki/"
    INTERPRO_URL="https://www.ebi.ac.uk/interpro/entry/InterPro/"
    PFAM_URL="https://www.ebi.ac.uk/interpro/entry/pfam/"
    PFAM_CLAN_URL="https://www.ebi.ac.uk/interpro/set/pfam/"
    TC_URL="https://www.tcdb.org/search/result.php?tc="
    EC_URL="https://enzyme.expasy.org/EC/"
    GO_URL="https://www.ebi.ac.uk/QuickGO/term/GO:"
    SO_URL="http://www.sequenceontology.org/browser/current_release/term/"
    KEGG_URL="https://www.genome.jp/entry/"
    BRENDA_EC_URL="https://www.brenda-enzymes.org/enzyme.php?ecno="
    COG_URL="https://www.ncbi.nlm.nih.gov/research/cog/cog/"
    COG_CAT_URL="https://www.ncbi.nlm.nih.gov/research/cog/cogcategory/"
    ARCOG_URL="http://eggnog6.embl.de/search/ogs/"
    PMID_URL="https://www.ncbi.nlm.nih.gov/pubmed/"
    CDD_URL="https://www.ncbi.nlm.nih.gov/Structure/cdd/"
    TAXID_URL="https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id="
    SNOMED_URL="https://snomedbrowser.com/Codes/Details/"
    BACDIVE_URL="https://bacdive.dsmz.de/strain/"
    HTTP_URL="http:"
    HTTPS_URL="https:"
    INTERRIDGE_URL="https://vents-data.interridge.org/ventfield/"
    PROSITE_URL="https://prosite.expasy.org/"
    PIRSF_URL="https://www.ebi.ac.uk/interpro/entry/pirsf/"
    TIGRFAMS_URL="https://www.ncbi.nlm.nih.gov/genome/annotation_prok/evidence/"
    SFLD_URL="https://www.ebi.ac.uk/interpro/entry/sfld/"
    SMART_URL="https://www.ebi.ac.uk/interpro/entry/smart/"
    HAMAP_URL="https://hamap.expasy.org/rule/"
    UNIPROTKB_QUERY_URL="https://www.uniprot.org/uniprotkb?query="

    def link_external_resource(resource, item, text=None):
      if text is None:
        text = item
      url = None
      if resource == "geonames":
          url = GEONAMES_URL + item
      elif resource in ["ENVO", "UBERON", "RO", "CHEBI", "OMP", "NCIT", "OHMI"]:
          url = OBO_URL + resource + "_" + item
      elif resource == "MICRO":
          url = MICRO_URL + item
      elif resource == "GO":
          url = GO_URL + item
      elif resource == "Wikipedia":
          url = WIKIPEDIA_URL + item
      elif resource == "Wiktionary":
          url = WIKTIONARY_URL + item
      elif resource == "taxid":
          url = TAXID_URL + item
      elif resource == "pmid" or resource == "PMID":
          url = PMID_URL + item
      elif resource == "sctid":
          url = SNOMED_URL + item
      elif resource == "bacdive":
          url = BACDIVE_URL + item
      elif resource == "interridge":
          url = INTERRIDGE_URL + item
      elif resource == "doi" or resource == "DOI":
          url = DOI_URL + item
      elif resource == "http":
          url = HTTP_URL + item
      elif resource == "https":
          url = HTTPS_URL + item
      elif resource == 'InterPro':
        url = INTERPRO_URL + item
      elif resource == 'TC':
        url = TC_URL + item
      elif resource == 'Pfam':
        url = PFAM_URL + item
      elif resource == 'Pfam_clan':
        url = PFAM_CLAN_URL + item
      elif resource == 'CDD':
        url = CDD_URL + item
      elif resource == 'EC':
        url = EC_URL + item
      elif resource == 'BRENDA_EC':
        url = BRENDA_EC_URL + item
      elif resource == 'SO':
        url = SO_URL + item
      elif resource == 'KEGG':
        url = KEGG_URL + item
      elif resource == 'COG_category':
        url = COG_CAT_URL + item
      elif resource == 'COG':
        url = COG_URL + item
      elif resource == 'arCOG':
        url = ARCOG_URL + item
      elif resource == 'PROSITE':
        url = PROSITE_URL + item
      elif resource == 'PIRSF':
        url = PIRSF_URL + item
      elif resource == 'TIGRFAMs':
        url = TIGRFAMS_URL + item
      elif resource == 'SFLD':
        url = SFLD_URL + item
      elif resource == 'SMART':
        url = SMART_URL + item
      elif resource == 'HAMAP':
        url = HAMAP_URL + item
      if url:
        return f"<a href='{url}' target='_blank'>{text}</a>"
      else:
        return None

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

    def uniprotkb_link(query):
      url = UNIPROTKB_QUERY_URL + query
      return f"<small>[&rightarrow;&nbsp;<a href='{url}' "+\
             "style='text-decoration: none' "+\
             "target='_blank'>UniProtKB</a>]</small>"

    def linked_unit_symbol(unit_type, symbol):
      if unit_type in ["specific_gene", "specific_protein", "function",
      "set:protein_complex"]:
        if symbol == ".":
          return symbol
        symq = urllib.parse.quote(symbol, safe='')
        query= f"query=(gene:{symq})%20OR%20(protein_name:{symq})"
        return symbol + " " + uniprotkb_link(query)
      else:
        return symbol

    def linked_unit_description(unit_type, description):
      if unit_type in ["specific_gene", "specific_protein", "function",
      "set:protein_complex"]:
        if description == ".":
          return description
        desq = description.replace("[", "(").replace("]", ")")
        desq = urllib.parse.quote(desq, safe='')
        return description + " " + uniprotkb_link(desq)
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
                  record_table='group', record_id=group_id,
                  related_table='group', related_id=rel_group,
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
                  record_table='unit', record_id=unit_id,
                  related_table='unit', related_id=rel_unit, prev='list_unit',
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
