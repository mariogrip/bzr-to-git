import subprocess, argparse
from debian.changelog import Changelog, Version
from datetime import *
from dateutil.tz import *
from git import Repo

parser = argparse.ArgumentParser(description='bzr to git')
parser.add_argument('bzr', type=str, help='bzr project to convert')
parser.add_argument("-d", "--dist", type=str, help="distribution to set for changelog")
parser.add_argument("-g", '--git', type=str, help="git remote url")
parser.add_argument("-p", "--push", action='store_true', help="do git push")
parser.add_argument("-b", "--branch", type=str, help="github branch to set (default: [dist])")
parser.add_argument("-o", "--outdir", type=str, help="output directory")

args = parser.parse_args()

outdir=args.outdir
if not args.outdir:
    outdir=args.bzr.split("/")[-1]

subprocess.call(["./do_convert.sh", args.bzr, outdir])
changelog_file = outdir+"/debian/changelog"

changelog = Changelog()
changelog.parse_changelog(open(changelog_file))

l_version_ = changelog.get_version()
l_version = l_version_.__str__()

r_version = l_version.split("+")[0]

# Bump version number to make sure we are one version above
if not "." in r_version:
    if r_version.isdigit():
        n_version = str(int(r_version)+1)
    else:
        n_version = r_version+"1"
else:
    dot_split = r_version.split(".")
    print(dot_split[-1].isdigit())
    if dot_split[-1].isdigit():
        dot_split[-1] = str(int(dot_split[-1])+1)
    else:
        dot_split[-1] = dot_split[-1]+"1"
    n_version = ".".join(dot_split)

# We only want the version and then replace that with +ubports
n_version = n_version+"+ubports"

# git-dch cannot handle "-" in changelog files, so make sure there is none
# is there is, destroy them!
n_version=n_version.replace("-", "")

dist = changelog.distributions
if args.dist:
    dist = args.dist

date_now = datetime.now(tzlocal()).strftime("%a, %d %b %Y %X %z")

changelog.new_block(package=changelog.get_package(),
                    version=Version(n_version),
                    distributions=dist,
                    urgency='medium',
                    author='UBports auto importer <infra@ubports.com>',
                    date=date_now,
                    )

changelog.add_change('');
changelog.add_change('  * Imported to UBports');
changelog.add_change('');

f = open(changelog_file, "w")
changelog.write_to_open_file(f)
f.close()

# Remove source format since jenkins does not support it
try:
    os.remove(outdir+"/debian/source/format")
except Exception as e:
    print("no source format to remove")

if args.git:
    repo = Repo(outdir)
    git = repo.git
    git.remote("add", "origin", args.git)
    branch=dist
    if args.branch:
        branch=args.branch
    git.checkout('HEAD', b=branch)
    git.add(A=True)
    git.commit(m="Imported to UBports")
    if args.push:
        git.push("origin", branch)
