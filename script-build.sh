# one-time if you’ve not created a builder:
docker buildx create --name multi-builder --use
docker buildx inspect --bootstrap

# login to your registry (Docker Hub example)
docker login

# build for both arches and push
export IMG=docker.io/meesam110/archprint:demo1
docker buildx build --platform linux/amd64,linux/arm64 -t $IMG --push .
docker buildx imagetools inspect $IMG
