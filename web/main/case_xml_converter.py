"""
Convert between XML and HTML versions of CAP's formatted case data.
"""

import lxml.sax
import lxml.html
import xml.sax

from lxml import etree

# sax functions passed to render_sax_tags
sax_start = lxml.sax.ElementTreeContentHandler.startElement
sax_end = lxml.sax.ElementTreeContentHandler.endElement
sax_chars = lxml.sax.ElementTreeContentHandler.characters

mapping = {
    "casebody": "section",
    "parties": "h4",
    "docketnumber": "p",
    "court": "p",
    "decisiondate": "p",
    "otherdate": "p",
    "attorneys": "p",
    "opinion": "article",
    "author": "p",
    "page-number": "a",
    "extracted-citation": "a",
    "bracketnum": "a",
    "footnotemark": "a",
}


def render_sax_tags(tag_stack):
    # run all of our commands, like "sax_start(*args)", to actually build the xml tree
    handler = lxml.sax.ElementTreeContentHandler()
    for method, args in tag_stack:
        method(handler, *args)
    return handler._root


class XmlToHtmlHandler(xml.sax.ContentHandler):
    def __init__(self, case_id):
        self.tag_stack = []
        self.case_id = case_id
        self.head_matter_open = False

    def startElement(self, name, attrs):

        if name == "casebody":
            self.tag_stack.append(
                (
                    sax_start,
                    (
                        "section",
                        {
                            "class": "casebody",
                            "data-case-id": self.case_id,
                            "data-firstpage": attrs["firstpage"],
                            "data-lastpage": attrs["lastpage"],
                        },
                    ),
                )
            )
            self.tag_stack.append((sax_chars, ("\n  ",)))
            self.tag_stack.append((sax_start, ("section", {"class": "head-matter"})))
            self.head_matter_open = True
        elif name == "opinion":
            if self.head_matter_open:
                self.close_head_matter()
            self.tag_stack.append(
                (sax_start, ("article", {"class": "opinion", "data-type": attrs["type"]}))
            )
        elif name == "page-number":
            label = attrs["label"]
            self.tag_stack.append(
                (
                    sax_start,
                    (
                        "a",
                        {
                            "id": "p" + label,
                            "href": f"#p{label}",
                            "data-label": label,
                            "data-citation-index": attrs["citation-index"],
                            "class": "page-label",
                        },
                    ),
                )
            )
        elif name == "extracted-citation":
            new_attrs = {"href": attrs["url"], "class": "citation", "data-index": attrs["index"]}
            if "case-ids" in attrs:
                new_attrs["data-case-ids"] = attrs["case-ids"]
            self.tag_stack.append((sax_start, ("a", new_attrs)))
        elif name in ("footnotemark", "bracketnum"):
            new_attrs = {"class": name}
            if "href" in attrs:
                new_attrs["href"] = attrs["href"]
            if "id" in attrs:
                new_attrs["id"] = attrs["id"]
            self.tag_stack.append((sax_start, ("a", new_attrs)))
        elif name in (
            "parties",
            "docketnumber",
            "court",
            "decisiondate",
            "otherdate",
            "attorneys",
            "author",
            "p",
            "blockquote",
        ):
            # content element
            attrs = {"id": attrs["id"]}
            if "data-blocks" in attrs:
                attrs["data-blocks"] = attrs["data-blocks"]
            if name not in ("p", "blockquote"):
                attrs["class"] = name
            new_name = "h4" if name == "parties" else "blockquote" if name == "blockquote" else "p"
            if self.head_matter_open:
                self.tag_stack.append((sax_chars, ("  ",)))
            self.tag_stack.append((sax_start, (new_name, attrs)))
        else:
            # passthrough
            self.tag_stack.append((sax_start, (name, attrs)))

    def characters(self, text):
        if self.head_matter_open and text == "    ":
            text = "      "
        self.tag_stack.append((sax_chars, (text,)))

    def endElement(self, name):
        if name == "casebody" and self.head_matter_open:
            self.close_head_matter()
        self.tag_stack.append((sax_end, (mapping.get(name, name),)))

    def close_head_matter(self):
        self.tag_stack.append((sax_end, ("section",)))
        self.tag_stack.append((sax_chars, ("\n  ",)))
        self.head_matter_open = False


def xml_to_html(input, case_id):
    handler = XmlToHtmlHandler(case_id)
    xml.sax.parseString(input, handler)
    tree = render_sax_tags(handler.tag_stack)
    return etree.tostring(tree, encoding=str, method="html")
