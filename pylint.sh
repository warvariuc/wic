# Note that pylint only searches your home directory and not the working directory for such a file.
pylint --rcfile=./.pylintrc --include-ids=y $*

# http://www.logilab.org/card/pylint_manual