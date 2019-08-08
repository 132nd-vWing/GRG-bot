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
JOIN = 'join'
KEYPAD = 'keypad'
NORTH = 'north'
NX = 'nx'
NY = 'ny'
SCALE_CORNER = 'scalecorner'
SCALE = 'scale'
TITLE = 'title'
WIDTH = 'width'

ARGUMENTS = (H_PAGES, V_PAGES, TITLE, KEYPAD, NORTH, NX, NY, WIDTH, SCALE, SCALE_CORNER)
FLAGS = (JOIN, )

client = discord.Client()
# fallback to test without docker
if not os.path.exists(config.BOTDIR):
    config.BOTDIR = os.path.abspath('./')


@client.event
async def on_ready() -> None:
    print('We have logged in as {0.user}'.format(client))


def parse_args(content: str) -> dict:
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
        WIDTH: 10.5,
        SCALE: 0.0,
        SCALE_CORNER: 0,
        JOIN: False,
    }
    argv = content.split(',')
    if len(argv) == 1 and '=' not in argv[0]:
        return args
    for arg in argv:
        if '=' in arg:
            keyword, val = arg.split('=')
            keyword = keyword.strip().lower()
            val = val.strip()
            if keyword in ARGUMENTS:
                args[keyword] = val
        else:
            arg = arg.strip().lower()
            if arg in FLAGS:
                args[arg] = True
            else:
                raise ValueError('I did not understand the option {}'.format(arg))
    for keyword in (H_PAGES, V_PAGES, KEYPAD, NORTH, NX, NY, SCALE_CORNER):
        args[keyword] = int(args[keyword])
    for keyword in (SCALE, WIDTH):
        args[keyword] = float(args[keyword])
    if (args[SCALE] > 0.01) and (args[SCALE_CORNER] == 0):
        args[SCALE_CORNER] = 2
    return args


def create_texfile(args: dict, path: str, filename: str, tex_name: str) -> None:
    with open(os.path.join(path, tex_name), 'w') as fd:
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
                scale = str(round(args[SCALE] / (args[NX] * args[H_PAGES]), 5))
                fd.write(
                    '[title={{{}}},keypad={},north={},ltrim={},rtrim={},ttrim={},btrim={},\
                    xstart={},ystart={},nx={},ny={}, width={}cm, scalex={}, \
                    scalecorner={}]{{{}}}'.format(
                        title, args[KEYPAD], args[NORTH], ltrim, rtrim, ttrim, btrim,
                        xstart, ystart, args[NX], args[NY], args[WIDTH],
                        scale, args[SCALE_CORNER], filename)
                )
                fd.write(r'\end{myenv}%' + '\n')
                page += 1
        fd.write(r'\end{document}')


@client.event
async def on_message(message: discord.Message) -> None:
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
        except Exception as e:
            await message.channel.send('I could not create the workdir. Pinging {}.'.format(os.environ['AUTHOR_ID']))
            print(e, traceback.format_exc())
            return
        # we first process it with the number of pages the user wanted
        try:
            tex_name = 'grg.tex'
            create_texfile(args, workdir, filename, tex_name)
            subprocess.call(
                [config.LATEX, '-halt-on-error', '-shell-escape', tex_name]
            )
        except Exception as e:
            await message.channel.send('I could not do the conversion. Pinging {}.'.format(os.environ['AUTHOR_ID']))
            print(e, traceback.format_exc())
            shutil.rmtree(workdir)
            return
        try:
            files = glob.glob(workdir + 'grg*.png') + glob.glob(workdir + 'grg*.pdf')
            files.sort()
            subprocess.call(
                [config.P7ZIP] + config.P7ZIP_ARGS + ['grg.7z'] + files
            )
            await message.channel.send(file=discord.File(workdir + 'grg.7z'))
            for f in files:
                os.remove(f)
        except Exception as e:
            await message.channel.send(
                'I could not zip and send the files. Pinging {}.'.format(os.environ['AUTHOR_ID'])
            )
            print(e, traceback.format_exc())
            shutil.rmtree(workdir)
            return
        # when the user also wants a single large GRG
        if args[JOIN]:
            tex_name = 'grg-single.tex'
            args = args
            args[NX] *= args[H_PAGES]
            args[NY] *= args[V_PAGES]
            args[WIDTH] = args[WIDTH] * args[H_PAGES]
            args[H_PAGES] = 1
            args[V_PAGES] = 1
            try:
                create_texfile(args, workdir, filename, tex_name)
                subprocess.call(
                    [config.LATEX, '-halt-on-error', '-shell-escape', tex_name]
                )
            except Exception as e:
                await message.channel.send('I could not do the conversion. Pinging {}.'.format(os.environ['AUTHOR_ID']))
                print(e, traceback.format_exc())
                shutil.rmtree(workdir)
                return
            try:
                files = glob.glob(workdir + 'grg*.png') + [workdir + 'grg*.pdf']
                files.sort()
                subprocess.call(
                    [config.P7ZIP] + config.P7ZIP_ARGS + ['grg-single.7z'] + files
                )
                await message.channel.send(file=discord.File(workdir + 'grg-single.7z'))
            except Exception as e:
                await message.channel.send(
                    'I could not zip and send the files. Pinging {}.'.format(os.environ['AUTHOR_ID'])
                )
                print(e, traceback.format_exc())
                shutil.rmtree(workdir)
                return
        shutil.rmtree(workdir)

    if len(message.attachments) == 0:
        await message.channel.send('Yes?')
        return


client.run(os.environ['TOKEN'])
