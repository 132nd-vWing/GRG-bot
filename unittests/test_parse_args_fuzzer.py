from subprocess import Popen, PIPE
from unittest.case import TestCase
import tempfile

from main import parse_args


class TestParseArgsFuzzer(TestCase):
    def test_basic_call(self):
        with tempfile.NamedTemporaryFile(delete=False) as fw:
            for i in range(1000):
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
        with open(fw.name, 'r') as fr:
            print(fr.read())
        ret = input('Looking good? [N, y] ')
        self.assertEqual(ret.lower().strip(), 'y')
