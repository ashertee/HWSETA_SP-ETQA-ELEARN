# -*- coding: utf-8 -*-
# from addons.base import wizard
from .common import PersonWizardCommon
from odoo.tests import new_test_user, tagged, Form
import time
DEBUG = True

if DEBUG:
    import logging

    logger = logging.getLogger(__name__)

    def dbg(*args):
        logger.info("".join([str(a) for a in args]))

else:

    def dbg(*args):
        pass


@tagged('hwseta')
class TestPersonWizards(PersonWizardCommon):



    def setUp(self):
        dbg("setup")
        super(TestPersonWizards, self).setUp()

    org_dict = {'sdl_no':'L987654321'}
    person_dict = {
        "person_title":"Mr",
        "person_last_name":"Bridge",
        "person_middle_name":"Pythagoras",

    }

    def test_person_registration_workflow(self):
        """
        use this as the main template for testing wizard workflows
        """
        person_env = self.env['person.wizard']
        james = new_test_user(self.env, login='hel', groups='seta_person.group_person_admin,base.group_system', name='Simple employee',
                              email='ric@example.com')
        person = person_env.with_user(james)
        # invoke the wizard
        Wizard0 = person.with_context(name="Guvna")
        # fill the wiz with our dict population
        wizard0 = Wizard0.create(self.person_dict)
        dbg(">>>>wizard0",wizard0)
        # submit the wizard and return the transaction
        confirmation_rec = wizard0.action_create()
        dbg("confirmation_rec>>>>",confirmation_rec)
        # confirm the values displayed and return the transaction
        ctxer = confirmation_rec["context"]
        res = self.env['confirm.application.wizard'].with_context(ctxer).create({})
        res = res.action_confirm()
        dbg("res confirmed",res)
        # read the master so we can compare to the originating data population
        res_vals = res.read()[0]

        for field, value in self.person_dict.items():
            dbg(self.assertEqual(value,res_vals[field]))
