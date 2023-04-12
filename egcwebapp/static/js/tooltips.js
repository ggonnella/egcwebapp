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

