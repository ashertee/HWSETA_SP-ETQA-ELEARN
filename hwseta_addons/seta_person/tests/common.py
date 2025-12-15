from odoo.tests.common import TransactionCase, HttpCase, tagged, Form


DEBUG = True

if DEBUG:
    import logging

    logger = logging.getLogger(__name__)

    def dbg(msg):
        logger.info(msg)

else:

    def dbg(msg):
        pass


@tagged('hwseta')
class PersonWizardCommon(TransactionCase):
    pass