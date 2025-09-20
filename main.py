import pandas as pd
import weaviate

from weaviate.classes.config import Configure 

CARDS_CSV_PATH = "all_mtg_cards.csv"

def create_cards_collection(client, should_recreate=False):

    if client.collections.exists("Cards") and should_recreate:
        client.collections.delete("Cards")

    client.collections.create(
        name="Cards",
        vector_config=Configure.Vectors.text2vec_ollama(
            api_endpoint="http://host.docker.internal:11434",
            model="nomic-embed-text",
        ),
    )

def add_cards_to_collection(client):
    cards = client.collections.use("Cards")

    with cards.batch.fixed_size(batch_size=200) as batch:
        with pd.read_csv(CARDS_CSV_PATH, chunksize=200) as reader:
            for chunk in reader:
                for index, row in chunk.iterrows():
                    print(f"Processing row {index}")
                    row_dict = preprocess_card_row(row)
                    if row_dict:
                        batch.add_object(row_dict)

                    if index > 100:
                        return

def preprocess_card_row(row):
    if not row["multiverse_id"]:
        return None
    return {
        "name": row["name"],
        "mana_cost": row["mana_cost"],
        "colors": row["colors"],
        "color_identity": row["color_identity"],
        "type": row["type"],
        "subtypes": row["subtypes"],
        "rarity": row["rarity"],
        "text": row["text"],
        "flavor": row["flavor"],
        "number": row["number"],
        "power": row["power"] if pd.notna(row["power"]) else None,
        "toughness": row["toughness"] if pd.notna(row["toughness"]) else None,
        "loyalty": row["loyalty"],
        "legalities": row["legalities"],
        "image_url": row["image_url"],
    }


if __name__ == "__main__":

    client = weaviate.connect_to_local()

    try:
        create_cards_collection(client)
        add_cards_to_collection(client)
    finally:
        client.close()