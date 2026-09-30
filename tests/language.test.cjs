const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('assets/js/language.js', 'utf8');

function visit({ path = '/', browser = 'en-US', preference, blocked = false } = {}) {
    const result = { redirect: null, preference, cleaned: null };
    vm.runInNewContext(source, {
        URL,
        document: { currentScript: { dataset: {
            home: String(path.split('?')[0].split('#')[0] === '/' || path.startsWith('/en/')),
            language: path.startsWith('/en/') ? 'en' : 'pl',
            english: '/en/',
        } } },
        navigator: { languages: [browser], language: browser },
        localStorage: {
            getItem() { if (blocked) throw Error('Blocked'); return preference; },
            setItem(key, value) { if (blocked) throw Error('Blocked'); result.preference = value; },
        },
        window: {
            location: { href: 'https://akorba.pl' + path, replace(url) { result.redirect = url; } },
            history: { replaceState(state, title, url) { result.cleaned = url; } },
        },
    });
    return result;
}

test('Polish browser stays on Polish homepage', () => {
    assert.equal(visit({ browser: 'pl-PL' }).redirect, null);
});
test('English and other browsers get English', () => {
    for (const browser of ['en-US', 'de-DE', 'fr', 'EN-gb']) {
        assert.equal(visit({ browser }).redirect, 'https://akorba.pl/en/');
    }
});
test('manual preference overrides browser language', () => {
    assert.equal(visit({ preference: 'pl' }).redirect, null);
    assert.equal(visit({ preference: 'en', browser: 'pl' }).redirect, 'https://akorba.pl/en/');
});
test('explicit Polish selection prevents bouncing back to English', () => {
    const result = visit({ path: '/?lang=pl', preference: 'en' });
    assert.equal(result.redirect, null);
    assert.equal(result.preference, 'pl');
    assert.equal(result.cleaned, 'https://akorba.pl/');
});
test('explicit English selection is saved', () => {
    assert.equal(visit({ path: '/en/?lang=en', browser: 'pl' }).preference, 'en');
});
test('direct English links and blog routes are not redirected', () => {
    for (const path of ['/en/', '/posts/', '/posts/array_python/', '/search/', '/tags/']) {
        assert.equal(visit({ path, preference: 'pl' }).redirect, null);
        assert.equal(visit({ path, preference: 'en' }).redirect, null);
    }
});
test('redirect keeps query parameters and section anchors', () => {
    assert.equal(visit({ path: '/?utm_source=test#kontakt' }).redirect,
        'https://akorba.pl/en/?utm_source=test#kontakt');
});
test('blocked storage does not break automatic or manual switching', () => {
    assert.equal(visit({ blocked: true }).redirect, 'https://akorba.pl/en/');
    assert.equal(visit({ path: '/?lang=pl', blocked: true }).redirect, null);
});
test('invalid preferences fall back to browser language', () => {
    assert.equal(visit({ preference: 'bad', browser: 'pl' }).redirect, null);
});
