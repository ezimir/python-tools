# -*- coding: utf-8 -*-


import argparse
argument_parser = argparse.ArgumentParser(description = 'Convert document to mobi format.', prog = 'python {}'.format(__file__))
argument_parser.add_argument('config_file', metavar='config-file', help = 'configuration file')
argument_parser.add_argument('output_file', metavar='output-file', help = 'name of output file without extension')

args = argument_parser.parse_args()


import sys
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

def error(message, errno = 1):
    """Exit with message."""

    print '{}ERROR: {}{}'.format(bcolors.FAIL, message, bcolors.ENDC)
    sys.exit(errno)

def warn(message):
    """Show warning message."""

    print '{}Warning: {}{}'.format(bcolors.WARNING, message, bcolors.ENDC)


try:
    print 'Loading config file "{}"'.format(args.config_file)
    config_file = open(args.config_file)

except IOError, e:
    error('Could not open config file', e.errno)

import json
config = json.load(open(args.config_file))
print 'Config loaded'


if hasattr(args, 'output_dir'):
    config['output_dir'] = args.output_dir

if 'output_dir' not in config:
    config['output_dir'] = 'output'
    warn('Using default output dir: "./{[output_dir]}/"'.format(config))


import os
import shutil


if os.path.exists(config['output_dir']):
    warn('Output directory exists -> removing')
    shutil.rmtree(config['output_dir'])



if hasattr(args, 'content_dir'):
    config['content_dir'] = args.content_dir

if 'content_dir' not in config:
    config['content_dir'] = 'Content'
    warn('Using default content dir: "{[content_dir]}"'.format(config))


print 'Creating directory structure for EPub'
os.mkdir(config['output_dir'])
os.mkdir(os.path.join(config['output_dir'], 'META-INF'))
os.mkdir(os.path.join(config['output_dir'], config['content_dir']))
os.mkdir(os.path.join(config['output_dir'], config['content_dir'], 'css'))



if hasattr(args, 'source_dir'):
    config['source_dir'] = args.source_dir

if 'source_dir' not in config:
    config['source_dir'] = '{}/source/'.format(os.path.dirname(__file__))
    warn('Using default source dir: "{[source_dir]}"'.format(config))


print 'Creating mandatory files'
open(os.path.join(config['output_dir'], 'mimetype'), 'w').write('application/epub+zip')

template = open(os.path.join(config['source_dir'], 'container.xml'), 'r').read()
xml = template.format(**config)
open(os.path.join(config['output_dir'], 'META-INF', 'container.xml'), 'w').write(xml)


if hasattr(args, 'style'):
    config['style'] = args.style

if 'style' not in config:
    config['style'] = os.path.join(config['source_dir'], 'style.css')


print 'Copying stylesheet'

style = open(config['style'], 'r').read()
open(os.path.join(config['output_dir'], config['content_dir'], 'css', 'style.css'), 'w').write(style)


print 'Building chapters'

template = unicode(open(os.path.join(config['source_dir'], 'chapter.xhtml'), 'r').read())
chapter_template = unicode(open(os.path.join(config['source_dir'], 'chapter.opf'), 'r').read())
spine_template = unicode(open(os.path.join(config['source_dir'], 'spine.opf'), 'r').read())
chapter_toc_template = unicode(open(os.path.join(config['source_dir'], 'chapter.ncx'), 'r').read())
chapters_xml = ''
spine_xml = ''
chapters_toc_xml = ''
for i, chapter in enumerate(config['chapters']):
    index = i + 1
    chapter['html'] = open(chapter['src'], 'r').read().decode('utf8')
    xml = template.format(chapter = chapter)
    open(os.path.join(config['output_dir'], config['content_dir'], 'chapter{}.xhtml'.format(index)), 'w').write(xml.encode('utf8'))
    chapters_xml += chapter_template.format(index = index)
    spine_xml += spine_template.format(index = index)
    chapters_toc_xml += chapter_toc_template.format(index = index, title = chapter['title'])

template = unicode(open(os.path.join(config['source_dir'], 'content.opf'), 'r').read())
xml = template.format(meta = config['meta'], chapters = chapters_xml.strip(), spine = spine_xml.strip())
open(os.path.join(config['output_dir'], config['content_dir'], 'content.opf'), 'w').write(xml.encode('utf8'))

template = unicode(open(os.path.join(config['source_dir'], 'toc.ncx'), 'r').read())
xml = template.format(meta = config['meta'], chapters = chapters_toc_xml.strip())
open(os.path.join(config['output_dir'], config['content_dir'], 'toc.ncx'), 'w').write(xml.encode('utf8'))


if os.path.exists('{}.epub'.format(args.output_file)):
    warn('Removing previous output file')
    os.unlink('{}.epub'.format(args.output_file))


from subprocess import call

working_dir = os.getcwd()
os.chdir(config['output_dir'])

print 'compiling EPub file: {}.epub'.format(args.output_file)

command = 'zip -r {}.epub mimetype META-INF {} -X -v'.format(args.output_file, config['content_dir'])
if call(command.split()):
    error('Could not compile zip file')

os.chdir(working_dir)


print 'Checking EPub file'
command = 'java -jar /Users/martin/Downloads/epubcheck-3.0b5/epubcheck-3.0b5.jar {}.epub'.format(args.output_file)
if call(command.split()):
    error('Can not create Mobi file, EPub has errors')


print 'Converting EPub to Mobi'
command = 'ebook-convert {0}.epub {0}.mobi --pretty-print'.format(args.output_file)
if call(command.split()):
    error('An error occured during conversion')

print 'Removing temporary output'
shutil.rmtree(config['output_dir'])
os.unlink('{}.epub'.format(args.output_file))


print 'Done'

