from unittest import TestCase

from main import parse_args, get_default_args
import arg


class TestParseArgs(TestCase):
    def test_empty(self):
        self.assertEqual(parse_args(''), get_default_args())
        self.assertEqual(parse_args('  '), get_default_args())
        self.assertEqual(parse_args('\n'), get_default_args())

    def test_single_arg(self):
        args1 = get_default_args()
        args1[arg.JOIN] = True
        args2 = parse_args('join')
        self.assertEqual(args1, args2)
        args1 = get_default_args()
        args1[arg.SCALE_CORNER] = 3
        args2 = parse_args('scalecorner=3')
        self.assertEqual(args1, args2)

    def test_wrong_keyword(self):
        with self.assertRaises(ValueError):
            parse_args('wfawr')
        with self.assertRaises(ValueError):
            parse_args('joi n')
        with self.assertRaises(ValueError):
            parse_args('scale=20.2, widht=10')

    def test_uppercase_lowercase(self):
        self.assertTrue(parse_args('scale=0.20') == parse_args('SCALE=0.20'))

    def test_spaces(self):
        self.assertTrue(parse_args('scale=0.20') == parse_args('scale = 0.20'))
        self.assertTrue(parse_args('scale=0.20') == parse_args('scale  =   0.20'))

    def test_additional_comma(self):
        self.assertTrue(parse_args(', h_pages=1') == get_default_args())
        self.assertTrue(parse_args(',, h_pages=1,') == get_default_args())
        self.assertTrue(parse_args(',, h_pages=1, v_pages=1, ') == get_default_args())

    def test_all_arguments(self):
        args1 = {
            arg.H_PAGES: 3,
            arg.V_PAGES: 2,
            arg.NORTH: 4,
            arg.KEYPAD: 2,
            arg.NX: 4,
            arg.NY: 6,
            arg.TITLE: 'AO QESHM',
            arg.SCALE_CORNER: 1,
            arg.SCALE: 2.0,
            arg.JOIN: True,
            arg.WIDTH: 9.0

        }
        args2 = parse_args(
            'h_pages=3, v_pages=2, north=4, nx=4, ny=6, title=AO QESHM, scale=2,' +
            'scalecorner=1, join, width = 9.0, keypad=2'
        )
        self.assertEqual(args1, args2)
