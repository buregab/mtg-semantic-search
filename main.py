import argparse
import ast
import json
import re

import pandas as pd
import weaviate

from weaviate.classes.config import Configure, DataType, Property

CARDS_CSV_PATH = "all_mtg_cards.csv"

COLOUR_MAP = {
    "W": "white",
    "U": "blue",
    "B": "black",
    "R": "red",
    "G": "green",
}


def expand_mana_cost(mana_cost):
    if pd.isna(mana_cost) or not mana_cost:
        return None

    symbols = re.findall(r"\{([^}]*)\}", str(mana_cost))
    if not symbols:
        return None

    expanded_parts = []

    for raw_symbol in symbols:
        symbol = raw_symbol.strip().upper()
        if not symbol:
            continue

        expanded = _expand_single_symbol(symbol)
        if expanded:
            expanded_parts.append(expanded)

    return ", ".join(expanded_parts) if expanded_parts else None


def _expand_single_symbol(symbol):
    if symbol.isdigit():
        value = int(symbol)
        return f"{value} colourless mana"

    if symbol in COLOUR_MAP:
        colour = COLOUR_MAP[symbol]
        return f"1 {colour} mana"

    if symbol == "C":
        return "1 colourless mana"

    if symbol == "S":
        return "1 snow mana"

    if symbol == "X":
        return "X mana"

    if symbol == "T":
        return "tap symbol"

    if symbol == "Q":
        return "untap symbol"

    if "/" in symbol:
        hybrid_parts = [_describe_hybrid_part(part) for part in symbol.split("/")]
        hybrid_parts = [part for part in hybrid_parts if part]
        if hybrid_parts:
            return f"{' or '.join(hybrid_parts)} hybrid mana"

    return symbol


def _describe_hybrid_part(part):
    part = part.upper().strip()

    if part.isdigit():
        return f"{int(part)} colourless"

    if part == "P":
        return "2 life"

    if part in COLOUR_MAP:
        return COLOUR_MAP[part]

    if part == "C":
        return "colourless"

    if part == "S":
        return "snow"

    return part


def create_cards_collection(client, should_recreate=False):

    if client.collections.exists("Cards") and should_recreate:
        client.collections.delete("Cards")

    client.collections.create(
        name="Cards",
        properties=[
            Property(name="name", data_type=DataType.TEXT),
            Property(name="mana_cost", data_type=DataType.TEXT, skip_vectorization=True),
            Property(name="mana_cost_text_expanded", data_type=DataType.TEXT),
            Property(name="colors", data_type=DataType.TEXT_ARRAY),
            Property(name="color_identity", data_type=DataType.TEXT_ARRAY),
            Property(name="type", data_type=DataType.TEXT),
            Property(name="subtypes", data_type=DataType.TEXT_ARRAY),
            Property(name="rarity", data_type=DataType.TEXT),
            Property(name="text", data_type=DataType.TEXT),
            Property(name="flavor", data_type=DataType.TEXT),
            Property(name="number", data_type=DataType.NUMBER, skip_vectorization=True),
            Property(name="power", data_type=DataType.TEXT),
            Property(name="toughness", data_type=DataType.TEXT),
            Property(name="loyalty", data_type=DataType.TEXT),
            # TODO parse legalities into an array of objects
            Property(name="legalities", data_type=DataType.TEXT, skip_vectorization=True), 
            Property(name="image_url", data_type=DataType.TEXT, skip_vectorization=True),
        ],
        vector_config=Configure.Vectors.text2vec_ollama(
            api_endpoint="http://host.docker.internal:11434",
            model="nomic-embed-text",
        ),
    )


def add_cards_to_collection(client, num_cards=None):
    cards = client.collections.use("Cards")

    with cards.batch.fixed_size(batch_size=200) as batch:
        with pd.read_csv(CARDS_CSV_PATH, chunksize=200) as reader:
            for chunk in reader:
                for index, row in chunk.iterrows():
                    print(f"Processing row {index}")
                    row_dict = preprocess_card_row(row)
                    if row_dict:
                        batch.add_object(row_dict)

                    if num_cards and index > num_cards:
                        return


def query_cards(client, query):
    cards = client.collections.use("Cards")
    response = cards.query.near_text(
        query=query,
        limit=3,
        distance=0.5
    )
    return response


def preprocess_card_row(row):
    if pd.isna(row["multiverse_id"]):
        return None
    # print(row)
    return {
        "name": row["name"],
        "mana_cost": row["mana_cost"],
        "mana_cost_text_expanded": expand_mana_cost(row["mana_cost"]),
        "colors": ast.literal_eval(row["colors"]) if pd.notna(row["colors"]) else None,
        "color_identity": ast.literal_eval(row["color_identity"]) if pd.notna(row["color_identity"]) else None,
        "type": row["type"],
        "subtypes": ast.literal_eval(row["subtypes"]) if pd.notna(row["subtypes"]) else None,
        "rarity": row["rarity"],
        "text": row["text"],
        "flavor": row["flavor"] if pd.notna(row["flavor"]) else None,
        "number": int(row["number"]) if pd.notna(row["number"]) else None,
        "power": row["power"] if pd.notna(row["power"]) else None,
        "toughness": row["toughness"] if pd.notna(row["toughness"]) else None,
        "loyalty": str(row["loyalty"]) if pd.notna(row["loyalty"]) else None,
        "legalities": row["legalities"],
        "image_url": row["image_url"],
    }


def main():
    parser = argparse.ArgumentParser(description="MTG semantic search tools")
    parser.add_argument("--query", type=str, help="Run a semantic search with the given query text")
    parser.add_argument(
        "--build-db",
        action="store_true",
        help="Rebuild the card collection in Weaviate using local card data",
    )
    parser.add_argument("--num-cards", type=int, help="Number of cards to add to the collection", default=None)

    args = parser.parse_args()

    if not args.build_db and not args.query:
        parser.error("at least one of --build-db or --query must be provided")

    client = weaviate.connect_to_local(
        host="weaviate",
        port=8080,
    )

    try:
        if args.build_db:
            create_cards_collection(client, should_recreate=True)
            add_cards_to_collection(client, num_cards=args.num_cards)

        if args.query:
            response = query_cards(client, args.query)
            for obj in response.objects:
                print(json.dumps(obj.properties, indent=2))
    finally:
        client.close()


if __name__ == "__main__":
    main()
