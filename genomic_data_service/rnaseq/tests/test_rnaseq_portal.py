import pytest


def test_rnaseq_portal_init():
    from genomic_data_service.rnaseq.domain.portal import Portal
    portal = Portal()
    assert isinstance(portal, Portal)
