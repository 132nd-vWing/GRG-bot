# GRG-bot: provide GRGs for maps via a discord bot
# Copyright © 2019, 2020 132nd.Professor
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

IMAGE_SIZE = '900x1200'

LATEX = 'pdflatex'

CONVERT = 'convert'
CONVERT_ARGS_PRE = [
    "-density", "300",
]
CONVERT_ARGS_POST = [
    "-filter", "box",
    "-resize", IMAGE_SIZE,
    "-gravity", "center",
    "-extent", IMAGE_SIZE,
    "-define", "png:compression-level=9",
    "-define", "png:compression-filter=1",
    "-define", "png:compression-strategy=0",
    "-sharpen", "0x0.5",
    "-depth", "8"
]

BOTDIR = '/app/'

P7ZIP = '7z'
P7ZIP_ARGS = [
    'a',
    '-t7z',
    '-m0=lzma2',
    '-mx=9',
    '-mfb=64',
    '-md=32m',
    '-ms=on',
]
