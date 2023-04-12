import { initTooltip } from "./tooltips.js";

export async function initDocumentInfoTooltip(target, pmid, url) {
  initTooltip(target, "article information",
    await getDocumentInfoTable(pmid, url));
}

function parseDocumentInfoJSON(json) {
  const {title, DOI, author, journal} = json;
  const journalTitle = json['container-title'] ? json['container-title'] : '';
  const volume = json.volume || '';
  const issue = json.issue || '';
  const page = json.page || '';
  const authors = author.map(a => a.given + ' ' + a.family).join(', ');

  return { title, DOI, authors, journalTitle, volume, issue, page };
}

function extractDoiFromUrl(url) {
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
  return null;
}

async function fetchDoiFromPmid(pmid) {
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
}

async function doiFromUrlOrPmid(url, pmid) {
  try {
    var doi = extractDoiFromUrl(url);
    if (!doi) {
      doi = await fetchDoiFromPmid(pmid);
    }
    return doi;
  } catch (error) {
    console.error(error);
    return "Error: Failed to fetch DOI";
  }
}

async function fetchDocumentInfoJSON(doi) {
  const url = `http://dx.doi.org/${doi}`;
  const headers = new Headers();
  headers.append("Accept", "application/json;q=1");
  const response = await fetch(url, { headers });
  if (!response.ok) {
    throw new Error("Failed to fetch JSON information");
  }
  return response.json();
}

const tooltipTemplate = (pmid, data) => `
  <table class="tooltip-table table-striped">
    <tr class="odd">
      <th>PMID</th>
      <td><a href="https://pubmed.ncbi.nlm.nih.gov/${pmid}/" target="_blank" class="no-underline pmid-link">${pmid}</a></td>
    </tr>
    <tr class="even">
      <th>DOI</th>
      <td><a href="https://dx.doi.org/${data.DOI}" target="_blank" class="no-underline doi-link">${data.DOI}</a></td>
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

async function getDocumentInfoTable(pmid, url) {
  try {
    const doi = await doiFromUrlOrPmid(url, pmid);
    const json = await fetchDocumentInfoJSON(doi);
    const data = parseDocumentInfoJSON(json);
    return tooltipTemplate(pmid, data);
  } catch (error) {
    console.error(error);
    return "Error: Failed to fetch article information";
  }
}
