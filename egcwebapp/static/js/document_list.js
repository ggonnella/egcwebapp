$(document).ready(function() {
  // Initialize DataTables
  $("#document-table").DataTable( {
    "drawCallback": function( settings ) {
      initTooltips();
    }
  });

  // Parse the JSON object
  function parseJSON(json) {
    const {title, DOI, author, journal} = json;
    const journalTitle = json['container-title'] ? json['container-title'] : '';
    const volume = json.volume || '';
    const issue = json.issue || '';
    const page = json.page || '';
    const authors = author.map(a => a.given + ' ' + a.family).join(', ');

    return { title, DOI, authors, journalTitle, volume, issue, page };
  }

  function initTooltips() {
    $(".document-info").each(function() {
      const $pmidCell = $(this).prev();
      const pmid = $pmidCell.text();

      // Fetch DOI using AJAX
      const fetchDoi = async () => {
        const url = $pmidCell.parent().next().find("a").attr("href");
        const doiMatch = url.match(/\/doi\/(.*?)(\?|$)/);
        if (doiMatch && doiMatch[1]) {
          console.log("Extracted DOI from URL:", doiMatch[1]);
          return doiMatch[1];
        }
        const doiMatch2 = url.match(/(\/|=)(10\..*?)(\?|$)/);
        if (doiMatch2 && doiMatch2[2]) {
          console.log("Extracted DOI from URL:", doiMatch2[2]);
          return doiMatch2[2];
        }
        const response = await fetch(
          `https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?ids=${pmid}`
        );
        if (!response.ok) {
          throw new Error("Failed to fetch DOI");
        }
        const xml = await response.text();
        const xmlDoc = $.parseXML(xml);
        const $xml = $(xmlDoc);
        const doi = $xml.find("record").attr("doi");
        if (!doi) {
          throw new Error("No DOI found");
        }
        return doi;
      };

      // Fetch JSON information using DOI
      const fetchJSONInfo = async (doi) => {
        const url = `http://dx.doi.org/${doi}`;
        const headers = new Headers();
        headers.append("Accept", "application/json;q=1");
        const response = await fetch(url, { headers });
        if (!response.ok) {
          throw new Error("Failed to fetch JSON information");
        }
        return response.json();
      };

      // Fetch content for the tooltip
      const fetchContent = async () => {
        const doi = await fetchDoi();
        if (!doi) {
          return "Failed to load DOI.";
        }
        const jsonData = await fetchJSONInfo(doi);
        const data = parseJSON(jsonData);

        const content = `
          <table class="tooltip-table table-striped">
            <tr class="odd">
              <th>PMID</th>
              <td>${pmid}</td>
            </tr>
            <tr class="even">
              <th>DOI</th>
              <td>${data.DOI}</td>
            </tr>
            <tr class="odd">
              <th>Title</th>
              <td>${data.title}</td>
            </tr>
            <tr class="even">
              <th>Authors</th>
              <td>${data.authors}</td>
            </tr>
            <tr class="odd">
              <th>Journal</th>
              <td>${data.journalTitle}</td>
            </tr>
            <tr class="even">
              <th>Volume</th>
              <td>${data.volume}</td>
            </tr>
            <tr class="odd">
              <th>Issue</th>
              <td>${data.issue}</td>
            </tr>
            <tr class="even">
              <th>Page</th>
              <td>${data.page}</td>
            </tr>
          </table>
        `;
        return content;
      };
      // Initialize Tippy.js tooltip
      tippy($(this)[0], {
        content: "Loading article information...",
        allowHTML: true,
        trigger: 'mouseenter click',
        interactive: true,
        hideOnClick: true,
        maxWidth: 700,
        onShow: async (instance) => {
          instance.setContent(await fetchContent());
        },
      });
    });
  }
});
