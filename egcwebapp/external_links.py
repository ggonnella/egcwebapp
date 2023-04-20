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

def link_uniprotkb_query(query):
  url = UNIPROTKB_QUERY_URL + query
  return f"<small>[&rightarrow;&nbsp;<a href='{url}' "+\
         "style='text-decoration: none' "+\
         "target='_blank'>UniProtKB</a>]</small>"
