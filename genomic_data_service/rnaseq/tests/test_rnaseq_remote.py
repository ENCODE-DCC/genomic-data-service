import pytest


def test_rnaseq_remote_portal_init():
    from genomic_data_service.rnaseq.remote.portal import Portal
    portal = Portal()
    assert isinstance(portal, Portal)


def test_rnaseq_remote_portal_get_rna_seq_files():
    from genomic_data_service.rnaseq.remote.portal import Portal
    portal = Portal()
    assert False
