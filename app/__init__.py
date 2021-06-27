import os

import peewee

import wic


app_dir = os.path.dirname(os.path.abspath(__file__))


class MainWindow(wic.main_window.MainWindow):

    def on_system_started(self):
        # predefined function called when the core is ready
        self.statusBar().showMessage('Ready...', 5000)
        # `<>` in the beginning of the string means to treat it as HTML
        self.printMessage(
            '<><b><span style="color: green">System started.</span> Welcome!</b>', True, False)
        print(f'Application directory: {app_dir}')

        wic.database = peewee.SqliteDatabase('app/databases/mtc.sqlite')
        wic.database_proxy.initialize(wic.database)
        # db = orm.SqliteAdapter('papp/databases/mtc.sqlite')

        from .reports import phone_number_search
        wic.forms.open_form(phone_number_search.Form)
        #self.mainWindow.restoreSubwindows()

    def onSystemAboutToExit(self):
        # a callback before shutdown
        # return False to cancel quitting
        return True

    def setupMenu(self):
        super().setupMenu()

        #Add actions for catalogs.
        # http://docs.python.org/library/pkgutil.html#pkgutil.walk_packages
        menu = self.menu.catalogs
        catalogs = (
            'persons.Person',
            'locations.Location',
            'districts.District',
            'regions.Region',
            'streets.Street',
        )
        for catalog in catalogs:
            model_path = f'app.catalogs.{catalog}'
            wic.menus.add_actions_to_menu(menu,
                wic.menus.create_action(
                    menu, catalog, lambda *args, p=model_path: wic.forms.catalog.open_catalog_form(p),
                    icon=':/icons/fugue/cards-address.png'))

        menu = self.menu.reports
        reports = ('phone_number_search', 'test', 'lissajous', 'repayment_schedule')
        for report in reports:
            report_name = report.capitalize()
            report_path = f'app.reports.{report}.Form'
            wic.menus.add_actions_to_menu(menu,
                wic.menus.create_action(
                    menu, report_name, lambda *args, p=report_path: wic.forms.open_form(p),
                    icon=':/icons/fugue/application-form.png'))


def test():
    wic._app.show_information(
        'test', 'This is a message from function `test` of the "global" module')
