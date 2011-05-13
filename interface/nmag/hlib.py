""" University of Southampton
 A class managing parameters for constructing hierarchical matrices
 with the programme library HLib.
 (C) 2009-05-21 Andreas Knittel
"""
import sys
from nmag_exceptions import *

class HMatrixSetup:
    """A class collecting the parameters needed in order to set up an HMatrix
    with HLib within Nmag.

    The optional argument ``algorithm`` is by default set to "HCA2".
    At present no other values are supported.
    The user can then specify a number of parameters in order to fine-tune
    the setup of the HMatrix. ``**kwargs`` stands for one or more of the
    following parameters (see `Hlib <http://www.hlib.org>`__ documentation
    for detailed descriptions of the parameers):

    :Parameters of HCA II:

        `eps_aca` : float
          A heuristic parameter which influences the accuracy of HCA II.
          By default this parameter is set to 1e-7

        `poly_order` : int
          A second parameter which influences the accuracy of the HCA II.
          Its default setting is 4.

    :Parameter for recompression algorithm:

        `eps` : float
          This parameter determines the accuracy of the recompression
          algorithm, which optimises a given hierarchical matrix.
          The default value is 0.001.

    :Parameters influencing the tree structure:

        `eta` : float
          eta is a parameter which influences the so called admissibility
          criterion. As explained above, a subblock of the boundary element
          matrix basically  describes the dipole potential at a cluster of
          surface nodes A generated by a different cluster B. The subblock
          can only be approximated when both cluster are spatially well
          separated. To have an objective measure of what 'well separated'
          means, an admissibility criterion has been introduced. The smaller
          the parameter eta is chosen, the more restrictive is the
          admissibility criterion. The default value is 2.0.

        `nmin` : int
          In order to be able to adjust the coarseness of the tree structure
          (a too fine tree structure would result in a higher amount of memory
          required for the storage of the tree itself), a parameter nmin has
          been introduced. It is the minimal number of lines or rows a
          submatrix within a leave can have, and is by default set to 30.

    :Parameter for the numerical quadrature:

        `quadorder` : int
          The order of the Gaussian quadrature used to compute matrix entries
          for the low-rank matrix blocks. For the matrix blocks, which are not
          approximated, an analytical expression instead of numerical
          integration is used. By default, quadorder is set to 3.

    """

    def __init__(self, algorithm="HCA2", **kwargs):
        if algorithm != "HCA2":
            raise NmagUserError("The only algorithm supported in HMatrixSetup"
                                " is HCA2.")

        self.parameters = {}

        self.parameters['ACA'] = {"algorithm":0, "eta":2.0, "nmin":30,
                                  "quadorder":3, "eps_aca":0.0001, "kmax":500,
                                  "eps":0.001}
        self.parameters['ACA+'] = {"algorithm":1, "eta":2.0, "nmin":30,
                                   "quadorder":3, "eps_aca":0.0001, "kmax":500,
                                   "eps":0.001}
        self.parameters['INT'] = {"algorithm":2, "eta":2.0, "nmin":30,
                                  "quadorder":3, "polyorder":5, "eps":0.001}
        self.parameters['HCA1'] = {"algorithm":3, "eta":2.0, "nmin":30,
                                   "quadorder":3, "eps_aca":0.0000001,
                                   "polyorder":6, "eps":0.001}
        self.parameters['HCA2'] = {"algorithm":4, "eta":2.0, "nmin":30,
                                   "quadorder":3, "eps_aca":0.0000001,
                                   "polyorder":4, "eps":0.001}

        if algorithm in self.parameters.keys():
            self.alg_param = self.parameters[algorithm]
        else:
            sys.stderr.write("The algorithm '%s' is not known. Known "
                             "algorithms are: %s" % (algorithm,
                                                     self.parameters.keys()))
            sys.exit()

        for item in kwargs.iterkeys():
            assert item in self.alg_param.iterkeys(), \
              "%s is not an argument for algorithm %s." % (item,algorithm)
            self.alg_param[item] = kwargs[item]

        self._hlib_param__ = {"algorithm":0, "nfdeg":0, "nmin":0,
                              "eta":0.0, "eps_aca":0.0, "eps":0.0,
                              "p":1, "kmax":0}

        self.paramnames_match = {"algorithm":"algorithm", "nmin":"nmin",
                                 "quadorder":"nfdeg", "eta":"eta",
                                 "eps_aca":"eps_aca", "eps":"eps",
                                 "polyorder":"p", "kmax":"kmax"}

        for item in self.alg_param.iterkeys():
            self._hlib_param__[self.paramnames_match[item]] = self.alg_param[item]

    def __repr__(self):
        s = ", ".join(["%s=%s" % key_val
                       for key_val in self.alg_param.iteritems()
                       if key_val[0] != "algorithm"])
        return "HMatrixSetup(%s)" % s

    def get_hlib_parameters_internal(self):
        """Returns the dictionary hlib_param_internal of hlib
        parameters and their corresponding values.

        """

        return self._hlib_param__

default_hmatrix_setup = HMatrixSetup()

def initialize_library(logmsg=None):
    import os
    import ocaml
    if logmsg == None:
        logmsg = lambda msg: None
        def logmsg(msg): print msg

    logmsg("Initialisation of HLib: looking for the library DLL...")
    pythonpath = os.getenv('PYTHONPATH')
    if pythonpath == None:
        logmsg("PYTHONPATH is not defined: Failure!")
        return False

    logmsg("PYTHONPATH is '%s'" % pythonpath)
    search_paths = pythonpath.split(':')

    for path in search_paths:
        logmsg("Searching inside '%s'" % path)
        if os.path.isdir(path):
            candidate = \
              os.path.join(path, 'extra', 'lib', 'libhmatrix-1.3.so')
            if os.path.isfile(candidate):
                logmsg("Found a candidate '%s'" % candidate)
                try:
                    ocaml.init_hlib(candidate)
                except:
                    return False
                return True

            else:
                logmsg("'%s' is not there!" % candidate)
    return False

