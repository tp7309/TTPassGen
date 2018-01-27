from fabric.api import local


def lint():
    local("flake8 .")
    local("yapf --style pep8 -i -r .")


def test():
    local("nosetests")


def commit():
    local("git add -A && git commit")


def push():
    local("git push")


def done():
    lint()
    test()
    commit()
    push()
