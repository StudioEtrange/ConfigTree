import os

from configtree import Walker, Updater
from configtree import formatter

update = Updater(namespace={"os": os})
walk = Walker(env=os.environ["ENV_NAME"])


@formatter.option(
    "indent",
    default=None,
    type=int,
    metavar="<indent>",
    help="indent size (default: %(default)s)",
)
def to_xml(tree, indent=None):
    """ Dummy XML formatter """

    def get_indent(level):
        if indent is None:
            return ""
        else:
            return " " * indent * level

    result = ["<configtree>"]
    for key, value in tree.items():
        result.append("%s<item>" % get_indent(1))
        result.append("%s<key>%s</key>" % (get_indent(2), key))
        result.append(
            '%s<value type="%s">%s</value>'
            % (get_indent(2), type(value).__name__, value)
        )
        result.append("%s</item>" % get_indent(1))
    result.append("</configtree>")
    if indent is None:
        return "".join(result)
    else:
        return os.linesep.join(result)


formatter.map["xml"] = to_xml
