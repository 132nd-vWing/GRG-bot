from subprocess import Popen, PIPE, call
from unittest.case import TestCase
from os import unlink
from tempfile import NamedTemporaryFile

from main import parse_args


class TestParseArgsFuzzer(TestCase):
    def test_basic_call(self):
        with NamedTemporaryFile(delete=False) as fw:
            for i in range(10000):
                p = Popen(['radamsa'], stdout=PIPE, stdin=PIPE, stderr=PIPE)
                try:
                    test_args = p.communicate(input='h_pages=2'.encode())[0]
                except:
                    pass
                else:
                    try:
                        with self.assertRaises(ValueError):
                            parse_args(test_args.decode())
                    except AssertionError:
                        fw.write(test_args + '\n'.encode())
                finally:
                    p.terminate()
        call('sort -u {}'.format(fw.name), shell=True)
        unlink(fw.name)
        ret = input('Looking good? [N, y] ')
        self.assertEqual(ret.lower().strip(), 'y')

"""
the following outputs are returned as valid, which constitutes an error: 

=1
1
2
h_pages
h_pages=
h_pages=2
 h_pages=2
h_pages=2
"""