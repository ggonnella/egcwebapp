// Initialize Tippy.js tooltip
export async function initTooltip(target, loading, content) {
  tippy(target[0], {
    content: "Loading " + loading + "...",
    allowHTML: true,
    trigger: 'mouseenter click',
    interactive: true,
    hideOnClick: true,
    maxWidth: 700,
    onShow: async (instance) => {
      instance.setContent(content);
    },
  });
}

export async function initEgcTooltips() {
  $(".egc-tooltip").each(async function () {
    await initTooltip($(this), "EGC data", $(this).data("content"));
  });
}

export async function initRelatedTooltips(infoclass, collection) {
  $(infoclass).each(async function() {
    const recordId = $(this).prev().data('related-id');
    try {
      const response = await fetch(`/api/${collection}/${recordId}`);
      if (!response.ok) {
        console.error(`Failed to fetch record information for ID ${recordId}`);
        return "<p>Error: Failed to fetch record information</p>";
      }
      const table = await response.text();
      const html = `<div class="tooltip-table">${table}</div>`
      initTooltip($(this), "Record", html);
    } catch (error) {
      console.error(`Failed to fetch record information for ID ${recordId}:`, error);
      return "<p>Error: Failed to fetch record information</p>";
    }
  });
}
