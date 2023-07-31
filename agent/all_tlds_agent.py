"""All TLDs agent implementation"""
import logging
from typing import Iterator

import tld
from ostorlab.agent import agent
from ostorlab.agent import definitions as agent_definitions
from ostorlab.agent.message import message as m
from ostorlab.agent.mixins import agent_persist_mixin
from ostorlab.runtimes import definitions as runtime_definitions
from rich import logging as rich_logging

logging.basicConfig(
    format="%(message)s",
    datefmt="[%X]",
    level="INFO",
    force=True,
    handlers=[rich_logging.RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger(__name__)

STORAGE_NAME = "agent_all_tlds_storage"


class AllTldsAgent(agent.Agent, agent_persist_mixin.AgentPersistMixin):
    """All TLDs agent."""

    def __init__(
        self,
        agent_definition: agent_definitions.AgentDefinition,
        agent_settings: runtime_definitions.AgentSettings,
    ) -> None:
        agent.Agent.__init__(self, agent_definition, agent_settings)
        agent_persist_mixin.AgentPersistMixin.__init__(self, agent_settings)

    def process(self, message: m.Message) -> None:
        """Generates all possible TLD iteration of a source domain.

        Args:
            message: Domain to process.

        Returns:
            None
        """
        name = message.data.get("name")
        if name is None:
            return

        logger.info("processing name %s", name)
        domain_tld = tld.get_tld(
            name, fix_protocol=True, as_object=True, fail_silently=True
        )
        if domain_tld is None:
            logger.warning("Failed to get TLD for: %s", name)
            return
        if self.set_add(STORAGE_NAME, domain_tld.domain) is False:
            return
        logger.info("generating tlds for %s", name)
        tlds = tld.get_tld_names()
        for t in _generate_tlds(tlds):
            self.emit("v3.asset.domain_name", {"name": f"{domain_tld.domain}{t}"})


def _generate_tlds(tlds) -> Iterator[str]:
    """Generates all TLDs iterations."""
    for root in tlds.values():
        node = root.root
        yield from _get_child_tlds("", node)


def _get_child_tlds(partial_tld, node) -> Iterator[str]:
    """Recursive implementation to compose TLDs with their children."""
    for c_tld, c_node in node.children.items():
        if c_tld == "*":
            # * TLD expect an extra string representing the TLD. This will not brute force them, so we ignore them.
            pass
        elif c_node.children is not None and "*" in c_node.children:
            pass
        elif c_node.private is True:
            pass
        else:
            new_tld = f".{c_tld}{partial_tld}"
            if c_node.leaf is True:
                yield new_tld
            else:
                yield from _get_child_tlds(new_tld, c_node)


if __name__ == "__main__":
    logger.info("starting agent ...")
    AllTldsAgent.main()
