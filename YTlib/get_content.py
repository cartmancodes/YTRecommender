"""
Driver script
"""

from optparse import OptionParser
from content_getter import ContentGetter

def get_opts():
    """Setup metod for OptionParser"""

    usage = "usage: %prog -c 'chill indie music' -p 10"
    parser = OptionParser(usage)

    parser.add_option("-c", "--content", dest="content",
                    help="Content relevant String")
    parser.add_option("-p", "--pages", type=int,
                    dest="pages", default=2,
                    help="Enter the number of pages to be scraped, default value = 2")
    (options, args) = parser.parse_args()

    # Exception handling
    if not options.content:
        parser.error("Content String is not provided")
    return options

if __name__ == "__main__":
    opts = get_opts()
    cg = ContentGetter(opts)
    content_list = cg.get_content()
    print("Quality Content List: ")
    print(content_list)
    
