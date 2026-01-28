# image_and_text_extractor

docker compose up -d --build
docker compose run --rm tests
docker compose exec api sh -lc "ls -la /shared_outputs"
docker compose down

#Inspect volume directly
docker run --rm -v image_and_text_extractor_shared_outputs:/shared_outputs alpine \
  sh -lc "find /shared_outputs -maxdepth 2 -type f -print"
