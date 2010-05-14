#!/usr/bin/python
# Nmag micromagnetic simulator
# Copyright (C) 2010 University of Southampton
# Hans Fangohr, Thomas Fischbacher, Matteo Franchin and others
#
# WEB:     http://nmag.soton.ac.uk
# CONTACT: nmag@soton.ac.uk
#
# AUTHOR(S) OF THIS FILE: Matteo Franchin
# LICENSE: GNU General Public License 2.0
#          (see <http://www.gnu.org/licenses/>)

version = "distmake-builder 0.1"
import os

def comment(text):
    return "\n".join(["# %s" % line for line in text.splitlines()])

class Script:
    def __init__(self):
        self.text = ""

    def writeln(self, line):
        self.text += line + "\n"

    def save(self, filename=""):
        fn = filename
        i = 0
        while True:
            if not os.path.exists(fn):
                f = open(fn, "w")
                f.write(self.text)
                f.close()
                return fn

            else:
                fn = "%s.%d" % (filename, i)
                i += 1

class ChoiceList:
    def __init__(self, desc):
        self.desc = desc
        self.choices = []

    def __str__(self):
        return "\n".join([str(c) for c in self.choices])

    def wait(self, text):
        print "="*40
        print text
        print "="*40
        print "Press [ENTER] to continue...",
        raw_input()

    def add_choice(self, choice):
        """Add a new choice to the Plan."""
        self.choices.append(choice)
        return choice

    def ask_user(self, script):
        self.wait(self.desc)

        for c in self.choices:
            c.ask_user(script)

    def save(self):
        pass

class Choice:
    def __init__(self, desc):
        self.desc = desc
        self.chosen = None
        self.should_ask_function = None
        self.alternatives = []

    def __str__(self):
        if self.chosen != None:
            return "Q: %s\n   %s" \
                   % (self.desc, str(self.alternatives[self.chosen]))
        else:
            return ""

    def when_should_ask(self, fn):
        self.should_ask_function = fn

    def add_alternative(self, alternative):
        self.alternatives.append(alternative)
        return alternative

    def ask_user(self, script):
        if self.should_ask_function != None:
            if not self.should_ask_function():
                return

        print "-"*40
        print self.desc
        for i, a in enumerate(self.alternatives):
            print "  (%d) %s" % (i, a.desc)

        while True:
            print "Please, enter a number between %d and %s:" \
                  % (0, len(self.alternatives)-1),

            try:
                choice = int(raw_input())
            except ValueError:
                pass
            else:
                if choice >= 0 and choice < len(self.alternatives):
                    self.chosen = choice
                    self.alternatives[choice].ask_user(script)
                    return


class Alternative:
    def __init__(self, desc):
        self.desc = desc

    def __str__(self):
        return self.desc

    def ask_user(self, script):
        pass

#=============================================================================
# Create the Plan object: we need to add all the possible choices a user may
# want to make and the code to use for each choice.
plan = ChoiceList("I'm now going to ask a few questions in order to build a "
                  "plan for making the distribution (a plan is just a shell "
                  "script that you can run to re-create the distribution so "
                  "that you don't need to answer the same questions again "
                  "and again).")

want_doc = plan.add_choice(Choice("Do you want to include documentation?"))
want_doc.add_alternative(Alternative("No, I'm concerned with size."))
want_doc.add_alternative(Alternative("Yes, include documentation."))

want_test = plan.add_choice(Choice("Do you want to include the test suite?"))
want_test.add_alternative(Alternative("No, I'm concerned with size."))
want_test.add_alternative(Alternative("Yes, include the big test suite."))

want_repo = plan.add_choice(Choice("Do you want to use the repositories?"))
want_repo.add_alternative(Alternative("No, I don't care about version "
                                      "control."))
want_repo.add_alternative(Alternative("Yes, I'm a developer, I want the "
                                      "repositories."))
repos = want_repo.add_alternative(ChoiceList("For each package (src, doc, test) "
                                             "I want do decide separately."))

distr = repos.add_choice(Choice("All-from-source repository: dist (Makefile "
                                "to build everything, including PETSc, etc)"))
distr.add_alternative(Alternative("Do not include version control for dist."))
distr.add_alternative(Alternative("Include version control for dist."))

srcr = repos.add_choice(Choice("Source repository: src"))
srcr.add_alternative(Alternative("Do not include version control for src."))
srcr.add_alternative(Alternative("Include version control for src."))

docr = repos.add_choice(Choice("Documentation repository: doc"))
docr.add_alternative(Alternative("Do not include version control for doc."))
docr.add_alternative(Alternative("Include version control for doc."))
docr.when_should_ask(lambda: want_doc.chosen == 1)

testr = repos.add_choice(Choice("Full test suite repository: test"))
testr.add_alternative(Alternative("Do not include version control for test."))
testr.add_alternative(Alternative("Include version control for test."))
testr.when_should_ask(lambda: want_test.chosen == 1)

want_tarb = plan.add_choice(Choice("Do you want a tarball or the directory?"))
want_tarb.add_alternative(Alternative("Give me just a tarball."))
want_tarb.add_alternative(Alternative("Give me just the corresponding directory."))
want_tarb.add_alternative(Alternative("Give me both."))

final = plan.add_choice(Choice("I collected enough information. What should I do:"))
final.add_alternative(Alternative("Create the distribution file(s)"))
final.add_alternative(Alternative("Generate a bash script to create the "
                                  "distribution file"))
final.add_alternative(Alternative("Do both things"))

#=============================================================================
# Ask the user to take decision and take note of the answers
script = Script()
plan.ask_user(script)


#=============================================================================
# Consider the answer and build the script
script.writeln("# Automatically generated using %s" % version)
script.writeln("# Script generated from the following answers:")
script.writeln(comment(str(plan)))
script.writeln(". disttools.sh")


from version import current
major, minor, patch = current[0]
if want_repo.chosen == 0:
    pkg_name = "nmag-%d.%d" % (major, minor)

else:
    pkg_name = "nmag-%d.%d-dev" % (major, minor)

script.writeln("PKGNAME=\"%s\"" % pkg_name)
script.writeln("allsrc_dev_compose \"$PKGNAME\" 'trunk'")

if want_doc.chosen:
    script.writeln('add_doc "$PKGNAME"')

if want_test.chosen:
    script.writeln('add_test "$PKGNAME"')

if want_repo.chosen != 1:
    if want_repo.chosen == 0:
        remove_dist_hg = True
        remove_src_hg = True
        remove_doc_hg = True
        remove_test_hg = True
    else:
        remove_dist_hg = (distr.chosen == 0)
        remove_src_hg = (srcr.chosen == 0)
        remove_doc_hg = (docr.chosen == 0)
        remove_test_hg = (testr.chosen == 0)

    if remove_src_hg:
        script.writeln('remove_hg "$PKGNAME"')

    if remove_src_hg:
        script.writeln('remove_hg "$PKGNAME/nsim"')
        script.writeln('remove_dir "$PKGNAME" nsim/admin nsim/devel nsim/obsolete '
                       'nsim/prototypes nsim/usersupport nsim/utils')

    if remove_test_hg:
        script.writeln('remove_hg "$PKGNAME/nsim/tests"')

    if remove_doc_hg:
        script.writeln('remove_hg "$PKGNAME/nsim/interface/nmag/manual"')

if want_tarb.chosen in [0, 2]:
    script.writeln('gen_tarball "$PKGNAME"')

if want_tarb.chosen == 0:
    script.writeln('remove_directory "$PKGNAME"')

#=============================================================================
# Save the script, execute it and show final messages
fn = script.save("distmake.bash")

if final.chosen in [0, 2]:
    os.system("/bin/bash %s" % fn)

if final.chosen == 0:
    try:
        os.remove(fn)
    except:
        print "Cannot remove '%s'" % fn

else:
    print "="*40
    print """I CREATED THE FILE '%s'"
    This is a bash file which generates the distribution file(s) according to your specifications.
    Use it as follows:

    /bin/bash %s
    """ % (fn, fn)