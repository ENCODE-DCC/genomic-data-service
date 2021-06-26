import pytest


def test_rnaseq_portal_init():
    from genomic_data_service.rnaseq.remote.portal import Portal
    portal = Portal()
    assert isinstance(portal, Portal)


def test_rnaseq_portal_get_data():
    from genomic_data_service.rnaseq.remote.portal import Portal
    portal = Portal()
    assert portal.get_data() == []
    assert False
