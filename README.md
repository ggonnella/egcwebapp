EGCWebapp is a web application for the visualization and (optionally) editing of
the information contained in EGC files.

# Starting the application

To start the application, clone the repository, change to
the main directory of it,
and run:
```
pip install -r requirements.txt  # install necessary dependencies
python3 egcwebapp/app.py         # start the application server
```

Leave the console open with the server running,
and enter the address mentioned in the console
in a web browser (e.g. http://127.0.0.1:5000).

By default the application is opened in read-write mode.
To disable editing, enter this before the python3 command:
```
export EGCWEBAPP_MODE="r"
```

# Using the application

First a file is uploaded using the ``Load file`` link in the top navigation bar.
Then one of the sections: ``Documents``, ``Extracts``, etc is selected from the bar.
The sections contain dynamic tables which are paginated and can be sorted by any
column. To search and filter the data, a general search box
is given on the top right (all fields), as well as search boxes for the
single columns, under the column headers.

From each table, one can navigate the graph of interconnected records of the EGC file,
by simply clicking on references of one record to another inside the table.
Links are opened as nested tables. From each record it is possible also to
open the list of records which refer to it.

## Editing mode

If editing is enabled, then new records can be created from the ``New Record``
button on the top right of the tables. For each record then some actions are available.
If there are no
references to the current record from other records, then it can be deleted.
Furthermore, the record can be edited (a nested editing form opens in the table)
and a (modified) copy of the record can be created (by opening it in the editing form,
changing the information and using the button ``Save as copy``.

After editing the EGC data,
the file with edited information can be downloaded from the ``Save File``
link in the top navigation bar. By default, the location of the original
file is shown, so that is can be overwritten by the modified version.

# About EGC

EGC is a format, which we developed, to represent rules of expectation
about the contents of genomes of prokaryotic organisms.
The format is described in a manuscript (available as preprint
at https://doi.org/10.48550/arXiv.2303.08758) and implemented as
TextFormats specification
(https://github.com/ggonnella/egc-spec). EGCtools
(https://github.com/ggonnella/egctools) is a Python library for
handling the format and EGCWebapp is based on it.

## Acknowledgements

This project has been created in context of the DFG project GO 3192/1-1
“Automated characterization of microbial genomes and metagenomes by collection
and verification of association rules”. The funders had no role in study
design, data collection and analysis.
