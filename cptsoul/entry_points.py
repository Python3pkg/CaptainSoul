# -*- coding: utf-8 -*-

import sys


def cptsoul():
    import sip
    sip.setapi("QString", 2)
    sip.setapi("QVariant", 2)
    import cptsoul.resources
    from cptsoul.application import CptsoulApp
    app = CptsoulApp()
    sys.exit(app.exec_())