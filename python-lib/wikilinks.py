'''
WikiLinks Extension for Python-Markdown
======================================
Converts [[WikiLinks]] to relative links.
See <https://pythonhosted.org/Markdown/extensions/wikilinks.html>
for documentation.
Original code Copyright [Waylan Limberg](http://achinghead.com/).
All changes Copyright The Python Markdown Project
License: [BSD](http://www.opensource.org/licenses/bsd-license.php)
'''
from __future__ import absolute_import
from __future__ import unicode_literals
from markdown.extensions import Extension
from markdown.inlinepatterns import Pattern
from markdown.util import etree
import re

class WikiLinkExtension(Extension):
    def __init__(self, *args, **kwargs):
        super(WikiLinkExtension, self).__init__(*args, **kwargs)
    def extendMarkdown(self, md, md_globals):
        WIKILINK_RE = r'\[\[([\u00a9\u00ae\u2000-\u3300\ud83c\ud000-\udfff\ud83d\ud000-\udfff\ud83e\ud000-\udfff\w\X0-9_ -]+)\]\]'
        wikilink_pattern = WikiLinks(WIKILINK_RE)
        md.inlinePatterns.add('wikilink', wikilink_pattern, "<not_strong")

class WikiLinks(Pattern):
    def __init__(self, pattern):
        super(WikiLinks, self).__init__(pattern)
    def handleMatch(self, m):
        if m.group(2).strip():
            label = m.group(2).strip()
            a = etree.Element('ac:link')
            ri = etree.SubElement(a, 'ri:page')
            ri.set('ri:content-title', label)
        else:
            a = ''
        return a
