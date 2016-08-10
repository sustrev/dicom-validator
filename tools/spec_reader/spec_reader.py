"""
SpecReader raeds information from DICOM standard files in docbook format as provided by ACR NEMA.
"""
import os

try:
    import xml.etree.cElementTree as ElementTree
except ImportError:
    import xml.etree.ElementTree as ElementTree


class SpecReaderError(Exception):
    pass


class SpecReaderFileError(SpecReaderError):
    pass


class SpecReaderParseError(SpecReaderError):
    pass


class SpecReaderLookupError(SpecReaderError):
    pass


class SpecReader(object):
    docbook_ns = '{http://docbook.org/ns/docbook}'

    def __init__(self, spec_dir):
        self.spec_dir = spec_dir
        self.part_nr = 0
        document_files = os.listdir(self.spec_dir)
        if not document_files:
            raise SpecReaderFileError(u'Missing docbook files in {}'.format(self.spec_dir))
        self._doc_trees = {}

    def _get_doc_tree(self):
        if self.part_nr not in self._doc_trees:
            doc_name = 'part{:02}.xml'.format(self.part_nr)
            document_files = os.listdir(self.spec_dir)
            if doc_name not in document_files:
                raise SpecReaderFileError(u'Missing docbook file {} in {}'.format(doc_name, self.spec_dir))
            try:
                self._doc_trees[self.part_nr] = ElementTree.parse(os.path.join(self.spec_dir, doc_name))
            except ElementTree.ParseError:
                raise SpecReaderFileError(u'Parse error in docbook file {} in {}'.format(doc_name, self.spec_dir))
        return self._doc_trees.get(self.part_nr)

    def _get_doc_root(self):
        doc_tree = self._get_doc_tree()
        if doc_tree:
            return doc_tree.getroot()

    def _find(self, node, elements):
        search_string = '/'.join([self.docbook_ns + element for element in elements])
        return node.find(search_string)

    def _findall(self, node, elements):
        search_string = '/'.join([self.docbook_ns + element for element in elements])
        return node.findall(search_string)

    def _get_ref_node(self, ref):
        element, label = ref.split('_')
        if element == 'sect':
            element = 'section'
        return self._get_doc_tree().find('//{}{}[@label="{}"]'.format(self.docbook_ns, element, label))

    def _find_text(self, node):
        try:
            text = self._find(node, ['para']).text
            if text and text.strip():
                return text.strip()
        except AttributeError:
            pass
        try:
            text = self._find(node, ['para', 'emphasis']).text
            if text and text.strip():
                return text.strip()
        except AttributeError:
            return ''

    def _get_tag_id(self, node):
        tag_ids = self._find_text(node)[1:-1].split(',')
        if len(tag_ids) == 2:
            try:
                return int(tag_ids[0], base=16), int(tag_ids[1], base=16)
            except ValueError:
                # todo: special handling for tags like 60xx
                pass
