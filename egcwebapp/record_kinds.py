record_kind_info = {
    'document': {"title": 'Document',
                 "record_types": ['D'],
                 "ref_by_kinds": ['extract']},
    'extract': {"title": 'Document Extract',
                "record_types": ['S', 'T'],
                "ref_by_kinds": ['crule', 'vrule']},
    'unit': {"title": "Unit",
             "record_types": ['U'],
             "ref_by_kinds": ['unit', 'attribute', 'model']},
    'attribute': {"title": "Attribute",
                  "record_types": ['A'],
                  "ref_by_kinds": ['vrule', 'crule']},
    'group': {"title": "Group",
              "record_types": ['G'],
              "ref_by_kinds": ['group', 'vrule', 'crule']},
    'model': {"title": "Model",
              "record_types": ['M'],
              "ref_by_kinds": []},
    'vrule': {"title": "Value Expectation Rule",
              "record_types": ['V'],
              "ref_by_kinds": []},
    'crule': {"title": "Comparative Expectation Rule",
              "record_types": ['C'],
              "ref_by_kinds": []},
}
