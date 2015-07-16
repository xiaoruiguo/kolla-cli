import logging

from kollaclient.i18n import _

from cliff.command import Command


class HostAdd(Command):
    "Host Add"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info(_("host add"))
        self.app.stdout.write(parsed_args)


class HostRemove(Command):
    "Host Remove"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info(_("host remove"))
        self.app.stdout.write(parsed_args)


class HostList(Command):
    "Host List"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info(_("host list"))
        self.app.stdout.write(parsed_args)


class HostSetzone(Command):
    "Host Setzone"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info(_("host setzone"))
        self.app.stdout.write(parsed_args)


class HostAddservice(Command):
    "Host Addservice"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info(_("host addservice"))
        self.app.stdout.write(parsed_args)


class HostRemoveservice(Command):
    "Host Removeservice"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info(_("host removeservice"))
        self.app.stdout.write(parsed_args)
