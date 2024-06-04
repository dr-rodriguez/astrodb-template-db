"""
Functions to test the database and example files
"""

from schema.schema_template import (
    Instruments,
    Names,
    Photometry,
    PhotometryFilters,
    Publications,
    Sources,
    Telescopes,
    Versions,
    Regimes
)

def test_setup_db(db):
    # Some setup tasks to ensure some data exists in the database first
    ref_data = [
        {
            "reference": "Ref 1",
            "doi": "10.1093/mnras/staa1522",
            "bibcode": "2020MNRAS.496.1922B",
        },
        {"reference": "Ref 2", "doi": "Doi2", "bibcode": "2012yCat.2311....0C"},
        {"reference": "Burn08", "doi": "Doi3", "bibcode": "2008MNRAS.391..320B"},
    ]

    source_data = [
        {"source": "Fake 1", "ra_deg": 9.0673755, "dec_deg": 18.352889, "reference": "Ref 1"},
        {"source": "Fake 2", "ra_deg": 9.0673755, "dec_deg": 18.352889, "reference": "Ref 1"},
        {"source": "Fake 3", "ra_deg": 9.0673755, "dec_deg": 18.352889, "reference": "Ref 2"},
    ]

    with db.engine.connect() as conn:
        conn.execute(db.Publications.insert().values(ref_data))
        conn.execute(db.Sources.insert().values(source_data))
        conn.commit()


def test_orm_use(db):
    # Tests validation using the SQLAlchemy ORM

    # Adding and removing a basic source
    s = Sources(source="V4046 Sgr", ra_deg=273.54, dec_deg=-32.79, reference="Ref 1")
    with db.session as session:
        session.add(s)
        session.commit()

    assert db.query(db.Sources).filter(db.Sources.c.source == "V4046 Sgr").count() == 1

    # Remove added source so other tests don't include it
    with db.session as session:
        session.delete(s)
        session.commit()

    assert db.query(db.Sources).filter(db.Sources.c.source == "V4046 Sgr").count() == 0


def test_photometry(db):
    
    # Confirm the source isn't already present
    assert db.query(db.Sources).filter(db.Sources.c.source == "Fake V4046 Sgr").count() == 0

    # Insert supporting data to (Sources, Publications, Telescopes, PhotometryFilters)
    s = Sources(source="V4046 Sgr", ra_deg=273.54, dec_deg=-32.79, reference="Ref 1")
    ref = Publications(reference="Cutri03")
    tel = Telescopes(telescope="Fake 2MASS", reference="Cutri03")
    pf = PhotometryFilters(band="Fake 2MASS.Ks", effective_wavelength_angstroms=2.159)
    reg = Regimes(regime="fake optical")

    with db.session as session:
        session.add_all([ref, pf, tel, s, reg])
        session.commit()

    # Verify supporting information was stored
    assert db.query(db.Sources).filter(db.Sources.c.source == "V4046 Sgr").count() == 1
    assert (
        db.query(db.Telescopes).filter(db.Telescopes.c.telescope == "Fake 2MASS").count()
        == 1
    )
    assert (
        db.query(db.PhotometryFilters)
        .filter(db.PhotometryFilters.c.band == "Fake 2MASS.Ks")
        .count()
        == 1
    )

    # Insert Photometry data, which refers to the supporting tables
    # Using it within add_all can cause issues since it may insert
    # the value before the supporting information is in place
    phot = Photometry(
        source="V4046 Sgr",
        band="Fake 2MASS.Ks",
        magnitude=7.249,
        telescope="Fake 2MASS",
        reference="Cutri03",
        regime="fake optical",
    )
    with db.session as session:
        session.add(phot)
        session.commit()

    # Verify Photometry was added
    assert (
        db.query(db.Photometry).filter(db.Photometry.c.source == "V4046 Sgr").count()
        == 1
    )

def test_coordinates(db):
    # Verify that all sources have valid coordinates
    t = (
        db.query(db.Sources.c.source, db.Sources.c.ra, db.Sources.c.dec)
        .filter(
            or_(
                db.Sources.c.ra.is_(None),
                db.Sources.c.ra < 0,
                db.Sources.c.ra > 360,
                db.Sources.c.dec.is_(None),
                db.Sources.c.dec < -90,
                db.Sources.c.dec > 90,
            )
        )
        .astropy()
    )

    if len(t) > 0:
        print(f"\n{len(t)} Sources failed coordinate checks")
        print(t)

    assert len(t) == 0, f"{len(t)} Sources failed coordinate checks"