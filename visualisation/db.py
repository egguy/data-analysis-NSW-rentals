import pandas as pd
from streamlit import cache_data
import streamlit as st
from streamlit.connections import BaseConnection
import duckdb


class DuckDBConnection(BaseConnection[duckdb.DuckDBPyConnection]):
    def _connect(self, **kwargs) -> duckdb.DuckDBPyConnection:
        if "database" in kwargs:
            db = kwargs.pop("database")
        else:
            db = self._secrets["database"]
        con = duckdb.connect(database=db, **kwargs)
        con.install_extension("spatial")
        con.load_extension("spatial")
        return con

    def cursor(self) -> duckdb.DuckDBPyConnection:
        return self._instance.cursor()

    def sql(self, query: str, ttl: int = 3600, **kwargs) -> duckdb.DuckDBPyRelation:
        # @cache_data(ttl=ttl)
        # def _query(query: str, **kwargs) -> duckdb.DuckDBPyRelation:
        #     cursor = self.cursor()
        #     cursor.sql(query, **kwargs)
        #     return cursor

        return self._instance.sql(query, **kwargs)

    def query(self, query: str, ttl: int = 3600, **kwargs) -> pd.DataFrame:
        @cache_data(ttl=ttl)
        def _query(query: str, **kwargs) -> pd.DataFrame:
            cursor = self.cursor()
            cursor.execute(query, **kwargs)
            return cursor.df()

        return _query(query, **kwargs)


def get_db() -> DuckDBConnection:
    return st.connection(
        "rentals", type=DuckDBConnection, database="rentals.duckdb", read_only=True
    )
