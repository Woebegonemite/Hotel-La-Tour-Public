# This file is the main driving force for connecting to the
# database by providing a setup for the database as well
# as a connection string and factory return function

import sqlalchemy as sa
import sqlalchemy.orm as orm
from main.data.model_base import SqlAlchemyBase

__factory = None


# Takes a connection string and sets up a SQLite connection
def global_init(db_file: str):
    global __factory

    if __factory:
        return

    if not db_file or not db_file.strip():
        raise Exception("Db file must be specified")

    connection_string = "sqlite:///" + db_file.strip()

    print(f"connecting to DB with {connection_string}")

    engine = sa.create_engine(connection_string, echo=False)

    __factory = orm.sessionmaker(bind=engine) #Creates a session

    import main.data.__all_models

    SqlAlchemyBase.metadata.create_all(engine) #Creates the database


# Returns the session
def create_session() -> orm.Session:
    global __factory
    return __factory()
