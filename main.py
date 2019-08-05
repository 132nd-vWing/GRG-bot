#!/usr/bin/python

import discord
import glob
import os
import shutil
import subprocess
import tempfile
import traceback

import config

H_PAGES = 'h_pages'
V_PAGES = 'v_pages'
TITLE = 'title'
KEYPAD = 'keypad'
NORTH = 'north'
NX = 'nx'
NY = 'ny'
WIDTH = 'width'
SCALE = 'scale'
SCALE_CORNER = 'scalecorner'
VALID_KEYWORDS = (H_PAGES, V_PAGES, TITLE, KEYPAD, NORTH, NX, NY, WIDTH, SCALE, SCALE_CORNER)

client = discord.Client()


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


def parse_args(content):
    """
    arguments must be comma separated
    understood keywords are defined in VALID_KEYWORDS

    :param content:
    :return: dict of arguments
    """
    args = {
        H_PAGES: 1,
        V_PAGES: 1,
        TITLE: '',
        KEYPAD: 1,
        NORTH: 3,
        NX: 6,
        NY: 8,
        WIDTH: '10.5cm',
        SCALE: 0.0,
        SCALE_CORNER: 0,
    }
    argv = content.split(',')
    if len(argv) == 1 and '=' not in argv[0]:
        return args
    for arg in argv:
        keyword, val = arg.split('=')
        keyword = keyword.strip().lower()
        val.strip().lower()
        if keyword in VALID_KEYWORDS:
            args[keyword] = val
        else:
            raise ValueError('I did not understand the keyword {}'.format(keyword))
    for keyword in (H_PAGES, V_PAGES, KEYPAD, NORTH, NX, NY, SCALE_CORNER):
        args[keyword] = int(args[keyword])
    args[SCALE] = float(args[SCALE])
    if (args[SCALE] > 0.01) and (args[SCALE_CORNER] == 0):
        args[SCALE_CORNER] = 2
    return args


def create_texfile(args, path, filename):
    with open(os.path.join(path, 'grg.tex'), 'w') as fd:
        fd.write(
            r'''\documentclass[%
              convert={true,density=300},%
              multi=myenv,%
              crop%
            ]{standalone}%
            \usepackage{grg}%
            \begin{document}%
            ''')
        number_pages = args[H_PAGES] * args[V_PAGES]
        page = 1
        for v in range(args[V_PAGES]):
            for h in range(args[H_PAGES]):
                if number_pages > 1:
                    title = '{} {}/{}'.format(args[TITLE], page, number_pages)
                else:
                    title = args[TITLE]
                ltrim = h / args[H_PAGES]
                rtrim = (1 - (h+1) / args[H_PAGES])
                btrim = v / args[V_PAGES]
                ttrim = (1 - (v+1) / args[V_PAGES])
                xstart = int(h * args[NX]) + 1
                ystart = int(v * args[NY]) + 1
                fd.write(r'\begin{myenv}\pagecolor{white}\grg')
                scale = str(round(args[SCALE] / (args[NX] * args[H_PAGES]), 2))
                fd.write(
                    '[title={{{}}},keypad={},north={},ltrim={},rtrim={},ttrim={},btrim={},\
                    xstart={},ystart={},nx={},ny={}, width={}, scalex={}, \
                    scalecorner={}]{{{}}}'.format(
                        title, args[KEYPAD], args[NORTH], ltrim, rtrim, ttrim, btrim,
                        xstart, ystart, args[NX], args[NY], args[WIDTH],
                        scale, args[SCALE_CORNER], filename)
                )
                fd.write(r'\end{myenv}%' + '\n')
                page += 1
        fd.write(r'\end{document}')


@client.event
async def on_message(message):
    try:
        if 'grg-bot' not in message.channel.name:
            return
    except AttributeError:  # happens when someone DMs the bot
        return

    if message.author == client.user:
        return

    if not message.content.startswith('!grg'):
        return

    if 'help' in message.content.lower():
        reply = 'Upload an image, and put "!grg" in the message.\n'
        reply += 'I understand the following keywords: h_pages, v_pages, title, keypad, north, nx, ny, width.\n'
        reply += 'Each keyword must be followed by "=" and the value. Multiple keywords must be separated by comma.\n'
        reply += 'Example: !grg title = AO Charlie, h_pages = 2, ny=10'
        await message.channel.send(reply)
        return

    for attachment in message.attachments:
        print('Received {} from {}'.format(attachment.filename, message.author))
        filename = attachment.filename
        basename, filetype = filename.split('.')
        if basename[:3].lower() == 'grg':
            await message.channel.send('Your filename cannot begin with grg.')
            return
        if filetype.lower() not in ('png', 'pdf', 'tif', 'tiff', 'jpg'):
            await message.channel.send('I cannot handle {} files.'.format(filetype))
            return
        try:
            args = parse_args(message.content[4:])  # remove leading '!grg'
        except Exception as e:
            await message.channel.send(str(e))
            print(e, traceback.format_exc())
            return
        try:
            workdir = tempfile.mkdtemp() + '/'
            await attachment.save(os.path.join(workdir + filename))
            os.chdir(workdir)
            os.symlink(os.path.join(config.BOTDIR, 'grg.sty'), 'grg.sty')
            create_texfile(args, workdir, filename)
        except Exception as e:
            await message.channel.send('I could not prepare the conversion. Pinging {}.'.format(os.environ['AUTHOR_ID']))
            print(e, traceback.format_exc())
            return
        with open(os.devnull, 'w') as FNULL:
            try:
                print('Converting')
                subprocess.call(
                    [config.LATEX, '-halt-on-error', '-shell-escape', 'grg.tex'],
                    stdout=FNULL
                )
            except Exception as e:
                await message.channel.send('I could not process the image. Pinging {}.'.format(os.environ['AUTHOR_ID']))
                print(e, traceback.format_exc())
                shutil.rmtree(workdir)
                return
            try:
                files = glob.glob(workdir + 'grg*.png') + [workdir + 'grg.pdf']
                files.sort()
                subprocess.call(
                    [config.P7ZIP, 'a', '-tzip', 'grg.zip'] + files,
                    stdout=FNULL
                )
                await message.channel.send(file=discord.File(workdir + 'grg.zip'))
            except Exception as e:
                await message.channel.send('I could not zip and send the files. Pinging {}.'.format(os.environ['AUTHOR_ID']))
                print(e, traceback.format_exc())
                return
            finally:
                shutil.rmtree(workdir)

    if len(message.attachments) == 0:
        await message.channel.send('Yes?')
        return

client.run(os.environ['TOKEN'])
