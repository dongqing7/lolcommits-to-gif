import os.path, time, datetime
import argparse
import shutil
import subprocess

from PIL import Image, ImageChops
from PIL.GifImagePlugin import getheader, getdata

class readable_dir(argparse.Action):
    def __call__(self,parser, namespace, values, option_string=None):
        prospective_dir=values
        if not os.path.isdir(prospective_dir):
            raise argparse.ArgumentTypeError("readable_dir:{0} is not a valid path".format(prospective_dir))
        if os.access(prospective_dir, os.R_OK):
            setattr(namespace,self.dest,prospective_dir)
        else:
            raise argparse.ArgumentTypeError("readable_dir:{0} is not a readable dir".format(prospective_dir))

parser = argparse.ArgumentParser(description='Create a timelapse')
parser.add_argument('directory', metavar='d', action=readable_dir,
                   help='the directory to use')

jpg_files = []

def last_modified(f):
    t = os.path.getctime(f)
    return datetime.datetime.fromtimestamp(t)

def by_date(tup_a, tup_b):
    a = os.path.join(*tup_a)
    b = os.path.join(*tup_b)
    if last_modified(a) > last_modified(b):
        return 1
    elif last_modified(a) < last_modified(b):
        return -1
    else:
        return 0

if __name__ == '__main__':
    tmp_directory = 'tmp'

    args = parser.parse_args()

    d = args.directory

    for root, dirs, files in os.walk(d):
        for f in files:
            if f.endswith('.jpg'):
                jpg_files.append((root, f))

    jpg_files.sort(cmp=by_date)

    # copy to tmp directory with sorted names:
    if os.path.exists(tmp_directory):
        shutil.rmtree(tmp_directory)

    os.makedirs(tmp_directory)

    for i, (root, f) in enumerate(jpg_files):
        print f, last_modified(os.path.join(root, f))
        shutil.copyfile(os.path.join(root, f), os.path.join(tmp_directory, "{0:08d}".format(i) + '.jpg'))

    # resize files so it goes faster
    p = subprocess.Popen('mogrify -format jpg -filter Cubic -resize 40%x40%  tmp/*.jpg', shell=True, stderr=subprocess.STDOUT)
    retval = p.wait()

    # do conversion to gif
    p = subprocess.Popen('convert -delay 20 -loop 0 -monitor tmp/*.jpg animation.gif', shell=True, stderr=subprocess.STDOUT)
    retval = p.wait()

    # remove tmp directory
    shutil.rmtree(tmp_directory)