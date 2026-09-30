# akorba.pl blog
[Link to the webpage](https://akorba.pl)

## Publishing in Polish and English

Hugo selects a post's language from its filename:

- `content/posts/my-topic.pl.md` → `/posts/my-topic/` (Polish)
- `content/posts/my-topic.en.md` → `/en/posts/my-topic/` (English)
- Existing `content/posts/my-topic.md` files default to Polish; no renaming or URL changes are needed.

Do not create both `my-topic.md` and `my-topic.pl.md`: they represent the same Polish page.
Language is not a tag; use `tags` only for topics.

Example English post (`content/posts/my-topic.en.md`):

```yaml
---
title: "My topic"
date: 2026-09-30
draft: false
tags: [Python]
---

English article text goes here.
```

Each language has its own blog listing, search index, tags and RSS feed. A post
can exist in just one language. The English blog displays an empty-state message
until its first published article.

Files sharing the same basename are linked as translations (for example,
`my-topic.md` and `my-topic.en.md`). If translations have different filenames,
give both the same `translationKey` in front matter. The PL / EN switch opens
the matching translation when available; otherwise it shows an explicit
`PL (blog)` or `EN (blog)` link to the other language's blog listing.

Automatic language selection applies only to the root homepage. Direct blog
and article links are never redirected. Manual language choices are remembered
when browser storage is available.

Landing page copy lives in `data/landing/pl.yaml` and `data/landing/en.yaml`.

## Validation

```sh
hugo --minify
node --test tests/language.test.cjs
python3 tests/multilingual_blog.py
```

The blog test builds a temporary copy with sample posts; it never publishes test
articles or changes the real content directory.
