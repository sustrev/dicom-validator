import os
import unittest

import pyfakefs.fake_filesystem_unittest

from tools.spec_reader.part3_reader import Part3Reader
from tools.spec_reader.spec_reader import SpecReaderLookupError, SpecReaderParseError, SpecReaderFileError


class ReadPart3Test(pyfakefs.fake_filesystem_unittest.TestCase):
    doc_contents = None

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(os.path.dirname(__file__), 'fixtures', 'part03_excerpt.xml'), 'rb') as f:
            cls.doc_contents = f.read()

    def setUp(self):
        super(ReadPart3Test, self).setUp()
        self.setUpPyfakefs()
        spec_path = os.path.join('dicom', 'specs')
        part3_path = os.path.join(spec_path, 'part03.xml')
        self.fs.CreateFile(part3_path, contents=self.doc_contents)
        self.reader = Part3Reader(spec_path)

    def test_read_empty_doc_file(self):
        spec_path = '/var/dicom/specs'
        os.makedirs(spec_path)
        self.fs.CreateFile(os.path.join(spec_path, 'part03.xml'))
        spec_reader = Part3Reader(spec_path)
        self.assertRaises(SpecReaderFileError, spec_reader.iod_description, 'A.16')

    def test_read_invalid_doc_file(self):
        spec_path = '/var/dicom/specs'
        os.makedirs(spec_path)
        self.fs.CreateFile(os.path.join(spec_path, 'part03.xml'), contents='Not an xml')
        spec_reader = Part3Reader(spec_path)
        self.assertRaises(SpecReaderFileError, spec_reader.iod_description, 'A.6')

    def test_read_incomplete_doc_file(self):
        spec_path = '/var/dicom/specs'
        os.makedirs(spec_path)
        self.fs.CreateFile(os.path.join(spec_path, 'part03.xml'),
                           contents='<book xmlns="http://docbook.org/ns/docbook">\n</book>')
        reader = Part3Reader(spec_path)
        self.assertRaises(SpecReaderParseError, reader.iod_description, 'A.6')

    def test_number_and_chapter_of_iods(self):
        iods = self.reader._get_iod_nodes()
        self.assertEqual(3, len(iods))
        self.assertTrue('A.3' in iods)
        self.assertFalse('A.38' in iods)
        self.assertTrue('A.38.1' in iods)

    def test_lookup_sop_class_by_chapter(self):
        self.assertRaises(SpecReaderLookupError, self.reader.iod_description, 'A.0')
        description = self.reader.iod_description(chapter='A.3')
        self.assertIsNotNone(description)
        self.assertTrue('title' in description)
        self.assertEqual(description['title'], 'Computed Tomography Image IOD')

    def test_get_iod_modules(self):
        description = self.reader.iod_description(chapter='A.38.1')
        self.assertIn('modules', description)
        modules = description['modules']
        self.assertEqual(27, len(modules))
        self.assertIn('General Equipment', modules)
        module = modules['General Equipment']
        self.assertEqual('C.7.5.1', module['ref'])
        self.assertEqual('M', module['use'])

    def test_iod_descriptions(self):
        descriptions = self.reader.iod_descriptions()
        self.assertEqual(3, len(descriptions))
        self.assertIn('A.3', descriptions)
        self.assertIn('A.18', descriptions)
        self.assertIn('A.38.1', descriptions)

    def test_module_description(self):
        self.assertRaises(SpecReaderLookupError, self.reader.module_description, 'C.9.9.9')
        description = self.reader.module_description('C.7.1.3')
        self.assertEqual(9, len(description))
        self.assertIn((0x0012, 0x0031), description)
        self.assertEqual('Clinical Trial Site Name', description[(0x0012, 0x0031)]['name'])
        self.assertEqual('2', description[(0x0012, 0x0031)]['type'])

    def test_sequence_in_module_description(self):
        description = self.reader.module_description('C.7.2.3')
        self.assertEqual(3, len(description))
        self.assertIn((0x0012, 0x0083), description)
        self.assertIn('items', description[(0x0012, 0x0083)])
        sequence_description = description[(0x0012, 0x0083)]['items']
        self.assertEqual(3, len(sequence_description))
        self.assertIn((0x0012, 0x0020), sequence_description)
        self.assertEqual('Clinical Trial Protocol ID', sequence_description[(0x0012, 0x0020)]['name'])
        self.assertEqual('1C', sequence_description[(0x0012, 0x0020)]['type'])

    def test_referenced_macro(self):
        description = self.reader.module_description('C.7.6.3')
        self.assertEqual(23, len(description))
        self.assertIn((0x0028, 0x7FE0), description)
        self.assertIn((0x7FE0, 0x0010), description)


if __name__ == '__main__':
    unittest.main()
