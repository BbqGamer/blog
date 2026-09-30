(() => {
    const config = document.currentScript.dataset;
    const url = new URL(window.location.href);
    const key = 'preferred-language';
    const explicit = url.searchParams.get('lang');
    let preferred;

    try {
        preferred = localStorage.getItem(key);
    } catch (_) {
        // Language links still work when browser storage is unavailable.
    }

    if (explicit === 'pl' || explicit === 'en') {
        try {
            localStorage.setItem(key, explicit);
        } catch (_) {}
        url.searchParams.delete('lang');
        window.history.replaceState(null, '', url.href);
        return;
    }

    // Only negotiate the Polish root homepage, never articles or direct /en/ links.
    if (config.home !== 'true' || config.language !== 'pl') return;

    if (preferred !== 'pl' && preferred !== 'en') {
        const browserLanguage = navigator.languages?.[0] || navigator.language || 'pl';
        preferred = /^pl(?:-|$)/i.test(browserLanguage) ? 'pl' : 'en';
    }

    if (preferred === 'en') {
        const destination = new URL(config.english, url);
        destination.search = url.search;
        destination.hash = url.hash;
        window.location.replace(destination.href);
    }
})();
