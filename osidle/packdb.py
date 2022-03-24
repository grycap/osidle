from .common import *
import argparse
from .version import VERSION
from .storage import Storage, remove_unneeded_data
import shutil
import os
import datetime
from tqdm import tqdm

def osidle_packdb():
    parser = argparse.ArgumentParser(allow_abbrev=False)

    parser.add_argument("-q", "--quiet", action="store_true" , help="use the quiet mode (suppress any output except from the resulting analysis)", default=False, dest="quiet")
    parser.add_argument("-y", "--yes", action="store_true", default=False, dest="force", help="answer yes to all questions")
    parser.add_argument("-n", "--no-backup", dest="backupdb", default=True, action="store_false", help="do not backup the database before packing it")
    parser.add_argument("-b", "--backup-filename", dest="backupfile", default=None, help="name of the file in which to store the backup")
    parser.add_argument("-o", "--overwrite", action="store_true", default=False, dest="overwrite", help="overwrite the backup file if it already exists")
    parser.add_argument("-F", "--keep-from", dest="keepfromdate", type=str, default=None, help="discard any sample before this date. Valid expressions are [<reference>-]<count>[suffix], where reference is a choice between the keywords 'now', 'begin', 'end', 'lastweek'... (if ommited, will be set to 'now'), and <suffix> may be a choice between 's', 'm', 'h', 'd', 'w', 'M' and 'y'. Default: 'begin' (i.e. beggining of the data)")
    parser.add_argument("-T", "--keep-to", dest="keeptodate", help="discard any sample after this date. The format is the same than '--keep-from' parameter. Default: 'now'", type=str, default=None)
    parser.add_argument("-d", "--database", dest="database", help="database to use", default="/var/lib/osidled/osidled.db")
    parser.add_argument("-v", "--verbose", dest="verbose", help="verbose", action="store_true", default=False)
    parser.add_argument("-vv", "--verbose-more", dest="verbosemore", help="verbose more", action="store_true", default=False)
    parser.add_argument("-m", "--minimize", dest="minimize", help="minimize the entries in the database", action="store_true", default=False)
    parser.add_argument('--version', action='version', version=VERSION)

    args = parser.parse_args()

    if not args.quiet:
        if args.verbose:
            setVerbose(1)
        if args.verbosemore:
            setVerbose(2)

    # Connect to the database (if possible)
    storage = Storage(args.database)
    storage.connect()

    # Get the begin and end time of the data
    p_debugv("getting information from the database")
    beginTime = storage.getmint()
    endTime = storage.getmaxt()

    p_debugv("begin time: {}".format(beginTime))
    p_debugv("end time: {}".format(endTime))

    if args.keepfromdate is not None:
        args.keepfromdate = toDate(args.keepfromdate, beginTime, endTime)
        p_debugv("keep-fromdate: ", args.keepfromdate)
        if args.keepfromdate is None:
            p_error("invalid expression for keep-fromdate")
            sys.exit(1)

    if args.keeptodate is not None:
        args.keeptodate = toDate(args.keeptodate, beginTime, endTime)
        p_debugv("keep-todate: ", args.keeptodate)
        if args.keeptodate is None:
            p_error("invalid expression for keep-todate")
            sys.exit(1)

    if not os.path.isabs(args.database):
        args.database = os.path.abspath(args.database)

    if not args.backupdb:
        if not args.force:
            if not user_yes_no_query("are you sure that you do not want to backup the database? (it will be modified and this action cannot be undone)".format(args.database), "n"):
                p_info("aborting the operation")
                sys.exit(0)
        else:
            p_debugv("forcing not backing up the database")

    if args.backupdb:
        if args.backupfile is None:
            args.backupfile = "{}/{}-{}".format(os.path.dirname(args.database), datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"), os.path.basename(args.database))

        backupfile = args.backupfile
        try:
            if os.path.exists(backupfile) and args.force:
                p_debugv("forcing overwriting the backup file")
                args.overwrite = True

            if os.path.exists(backupfile) and not args.overwrite:
                args.overwrite = user_yes_no_query("backup file {} already exists. Overwrite it?".format(backupfile), "n")

            if os.path.exists(backupfile) and not args.overwrite:
                p_error("not overwritting backup file {}".format(backupfile))
                sys.exit(1)

            p_info("backing up database to file {}".format(backupfile))
            shutil.copyfile(args.database, backupfile)
        except Exception as e:
            p_error("could not backup database: {}".format(e))
            sys.exit(1)
    else:
        p_info("not backing up database ")
    
    if not args.force:
        if not user_yes_no_query("are you sure that you want to pack the database? (it will be modified and this action cannot be undone)".format(args.database), "n"):
            p_info("aborting the operation")
            sys.exit(0)

    if (args.keepfromdate is not None) or (args.keeptodate is not None):
        rows = storage.delete(args.keepfromdate, args.keeptodate)
        p_info("{} rows deleted".format(rows))

    def prefilter(rowcount):
        global pbar
        if not args.quiet:
            pbar = tqdm(total=rowcount, desc="Processing entries", unit="entries")

    def postfilter():
        if not args.quiet:
            global pbar
            pbar.close()

    def filterdata(vmid, t, data):
        if not args.quiet:
            global pbar
            pbar.update(1)
        result = remove_unneeded_data(data)
        return result

    if args.minimize:
        storage.filterdata(filterdata, prefilter, postfilter)

    storage.vaccuum()
    p_info("database vaccuumed")
    try:
        pass
    except Exception as e:
        p_error("database packing failed: {}".format(e))
        sys.exit(1)
    # newfname = os.path.dirname(args.database) + "/osidled.db.new"