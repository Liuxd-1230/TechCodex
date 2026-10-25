"""Conservative text-layer screening, shared by preprocessing and retrieval."""
import unicodedata


def text_layer_quality(page):
    text = page.get_text(sort=True)
    visible = ''.join(text.split())
    bad = sum(c == '\ufffd' or unicodedata.category(c) in ('Co','Cc') for c in visible)
    readable = sum(c.isalnum() for c in visible)
    coverage = max((min(1, abs((r['bbox'][2]-r['bbox'][0]) * (r['bbox'][3]-r['bbox'][1])) /
                        max(1, page.rect.width*page.rect.height)) for r in page.get_image_info()), default=0)
    reasons = []
    if len(visible) < 40:
        reasons.append('missing or too little extracted text')
    if bad / max(1,len(visible)) > .02:
        reasons.append('replacement, private-use or control characters')
    if readable / max(1,len(visible)) < .35:
        reasons.append('too few readable letters/numbers')
    if coverage > .60 and len(visible) < 200:
        reasons.append('page-sized scan with only a short partial text layer')
    return {'reliable': not reasons, 'reasons': reasons, 'characters': len(visible),
            'image_coverage': round(coverage,4)}
