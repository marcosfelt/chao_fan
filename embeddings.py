from chao_fan.integrations.llama import get_model
import sqlite3
import sqlite_vss
import numpy as np
import time

# model = get_model(llama_kwargs=dict(embedding=True, verbose=False))
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


BATCH_SIZE = 5
EMBEDDING_ITERATIONS = 20


def create_tables(db: sqlite3.Connection):
    (version,) = db.execute("select vss_version()").fetchone()
    print("VSS version", version)

    db.execute(
        """
        CREATE TABLE articles(
            headline text,
            headline_embedding blob
        )
        """
    )
    db.execute(
        """
        CREATE VIRTUAL TABLE vss_articles 
        USING vss0(headline_embedding(384))
        """
    )

    with open("headlines.txt") as f:
        headlines = f.read().splitlines()
    db.executemany(
        "insert into articles(headline) VALUES(?)",
        [(headline,) for headline in headlines],
    )
    db.commit()


def create_embeddings(db: sqlite3.Connection):
    i = 0
    while i < EMBEDDING_ITERATIONS:
        batch = db.execute(
            """
            select rowid, headline
            from articles
            where headline_embedding is null
            limit ?
            """,
            [BATCH_SIZE],
        ).fetchall()
        if len(batch) == 0:
            break
        rowids = list(map(lambda x: x[0], batch))
        headlines = list(map(lambda x: x[1], batch))
        try:
            print(headlines)
            # time.sleep(2)
            # embedding_response = model.model.create_embedding(headlines)
            # embeddings = [
            #     np.array(embed["embedding"]) for embed in embedding_response["data"]
            # ]
            embeddings = model.encode(headlines)
            print("First 10 positions of first embedding:", embeddings[0, :10])
            print("Embedding shape:", embeddings[0].shape)
            for rowid, embedding in zip(rowids, embeddings):
                db.execute(
                    """
                    UPDATE articles
                    SET headline_embedding = ?
                    WHERE rowid = ?
                    """,
                    [embedding.tobytes(), rowid],
                )
                db.commit()
        except ZeroDivisionError as e:
            print(e)
        i += 1

    db.execute(
        """
        INSERT INTO vss_articles(rowid, headline_embedding)
        SELECT rowid, headline_embedding
        FROM articles
        """
    )
    db.commit()


def query_embeddings(db: sqlite3.Connection):
    row_id = 2
    result = db.execute(
        """
        SELECT  rowid, headline
        FROM articles
        WHERE rowid = ?
        """,
        [row_id],
    ).fetchone()
    print("Original headline:", result)
    results = db.execute(
        """
        SELECT articles.rowid, articles.headline, matches.distance, matches.headline_embedding
        FROM articles
        INNER JOIN (
            SELECT rowid, distance, headline_embedding
            FROM vss_articles
            WHERE vss_search(
                headline_embedding,
                (SELECT headline_embedding FROM articles WHERE rowid = ?)
            ) AND distance > 0
            ORDER BY distance
            LIMIT 10
        ) AS matches ON articles.rowid = matches.rowid
        """,
        [row_id],
    ).fetchall()
    print(
        "".join(
            [
                f"ID: {rowid} | Headline: {headline} | Distance {distance:.02f}\n"
                for rowid, headline, distance, embedding in results
            ]
        )
    )


if __name__ == "__main__":
    db = sqlite3.connect("embeddings.db")
    db.enable_load_extension(True)
    sqlite_vss.load(db)
    # create_tables(db)
    # create_embeddings(db)
    # result = db.execute(
    #     """
    #     SELECT COUNT(*)
    #     FROM vss_articles
    #     WHERE headline_embedding IS NOT NULL
    #     """
    # ).fetchall()
    # print("Rows with headline embeddings:", result[0])
    # result = db.execute(
    #     """
    #     SELECT rowid, headline, headline_embedding
    #     FROM articles
    #     """
    # ).fetchone()
    # print("Example:")
    # print(
    #     f"ID: {result[0]} | Headline: {result[1]} | Embedding (1st 10 positions): {np.frombuffer(result[2])[:10]}"
    # )
    query_embeddings(db)
    db.close()
