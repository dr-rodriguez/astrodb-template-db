# Build Galaxies-DB

import os
from astrodb_utils.loaders import DatabaseSettings
from astrodbkit.astrodb import create_database, Database

if __name__ == "__main__":
    # Read and validate the database settings
    db_settings = DatabaseSettings(settings_file="database.toml")

    db_file = db_settings.db_name + ".sqlite"

    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"Removed old database file {db_file}.")

    print(f"Creating new database file: {db_file}")
    db_connection_string = "sqlite:///" + db_file

    # Create database
    create_database(db_connection_string, felis_schema=db_settings.felis_path)

    # Connect and load the database
    # Customize for Galaxies/galaxy primary table
    db = Database(
        db_connection_string,
        reference_tables=db_settings.lookup_tables,
        primary_table="Galaxies",
        primary_table_key="galaxy",
        foreign_key="galaxy"
    )

    db.load_database(db_settings.data_path, verbose=True)
