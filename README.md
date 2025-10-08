# Local Development

## Docker

Uses the cloud weaviate instance to retrieve cards.

1. `docker buildx build -t mtg-semantic-search -f dev/Dockerfile .`
2. `docker run -p 5001:5000 mtg-semantic-search`

## Docker Compose

TODO

Will use the local weaviate instanceto retrieve cards.
