#!/usr/bin/python

import discord
import glob
import os
import shutil
import subprocess
import tempfile
import traceback

import arg
import config
import help

client = discord.Client()
# fallback to test without docker
if not os.path.exists(config.BOTDIR):
    config.BOTDIR = os.path.abspath('./')


@client.event
async def on_ready() -> None:
    print('We have logged in as {0.user}'.format(client))


def get_default_args() -> dict:
    args = {
        arg.H_PAGES: 1,
        arg.V_PAGES: 1,
        arg.TITLE: '',
        arg.KEYPAD: 1,
        arg.NORTH: 3,
        arg.NX: 6,
        arg.NY: 8,
        arg.WIDTH: 10.5,
        arg.SCALE: 0.0,
        arg.SCALE_CORNER: 0,
        arg.JOIN: False,
    }
    return args


def parse_args(content: str) -> dict:
    """
    arguments must be comma separated
    understood keywords are defined in ARGUMENTS and FLAGS
    :param content: string of arguments from the discord message
    :return: dict of arguments
    """
    args = get_default_args()
    argv = content.split(',')
    if len(argv) == 1 and len(argv[0].strip()) == 0:
        return args
    for one_arg in argv:
        if '=' in one_arg:
            keyword, val = one_arg.split('=')
            keyword = keyword.strip().lower()
            val = val.strip()
            if keyword in arg.ARGUMENTS:
                args[keyword] = val
            else:
                raise ValueError('I did not understand the argument {}'.format(one_arg))
        else:
            one_arg = one_arg.strip().lower()
            if one_arg in arg.FLAGS:
                args[one_arg] = True
            else:
                raise ValueError('I did not understand the flag {}'.format(one_arg))
    for keyword in (arg.H_PAGES, arg.V_PAGES, arg.KEYPAD, arg.NORTH, arg.NX, arg.NY, arg.SCALE_CORNER):
        args[keyword] = int(args[keyword])
    for keyword in (arg.SCALE, arg.WIDTH):
        args[keyword] = float(args[keyword])
    if (args[arg.SCALE] > 0.01) and (args[arg.SCALE_CORNER] == 0):
        args[arg.SCALE_CORNER] = 2
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
        number_pages = args[arg.H_PAGES] * args[arg.V_PAGES]
        page = 1
        for v in range(args[arg.V_PAGES]):
            for h in range(args[arg.H_PAGES]):
                if number_pages > 1:
                    title = '{} {}/{}'.format(args[arg.TITLE], page, number_pages)
                else:
                    title = args[arg.TITLE]
                ltrim = h / args[arg.H_PAGES]
                rtrim = (1 - (h+1) / args[arg.H_PAGES])
                btrim = v / args[arg.V_PAGES]
                ttrim = (1 - (v+1) / args[arg.V_PAGES])
                xstart = int(h * args[arg.NX]) + 1
                ystart = int(v * args[arg.NY]) + 1
                fd.write(r'\begin{myenv}\pagecolor{white}\grg')
                scale = str(round(args[arg.SCALE] / (args[arg.NX] * args[arg.H_PAGES]), 5))
                fd.write(
                    '[title={{{}}},keypad={},north={},ltrim={},rtrim={},ttrim={},btrim={},\
                    xstart={},ystart={},nx={},ny={}, width={}cm, scalex={}, \
                    scalecorner={}]{{{}}}'.format(
                        title, args[arg.KEYPAD], args[arg.NORTH], ltrim, rtrim, ttrim, btrim,
                        xstart, ystart, args[arg.NX], args[arg.NY], args[arg.WIDTH],
                        scale, args[arg.SCALE_CORNER], filename)
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
        await message.channel.send(help.help_message)
        return

    if 'version' in message.content.lower():
        try:
            with open('version.txt') as fd:
                await message.channel.send(fd.read())
        except FileNotFoundError:
            await message.channel.send('Could not determine version.')
        finally:
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
        if args[arg.JOIN]:
            tex_name = 'grg-single.tex'
            args = args
            args[arg.NX] *= args[arg.H_PAGES]
            args[arg.NY] *= args[arg.V_PAGES]
            args[arg.WIDTH] = args[arg.WIDTH] * args[arg.H_PAGES]
            args[arg.H_PAGES] = 1
            args[arg.V_PAGES] = 1
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
        await message.channel.send('At your service. If you need help, try `!grg help`.')


if __name__ == '__main__':
    client.run(os.environ['TOKEN'])
