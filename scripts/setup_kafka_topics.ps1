$ErrorActionPreference = "Stop"

$containerName = "lab04-kafka"
$bootstrapServer = "localhost:9092"

$topics = @(
    "diffusers.cpg.nodes.v1",
    "diffusers.cpg.edges.v1",
    "diffusers.source.metadata.v1",
    "diffusers.parser.errors.v1"
)

Write-Host "Đang kiểm tra Kafka container..."

$running = docker inspect `
    -f "{{.State.Running}}" `
    $containerName 2>$null

if ($running -ne "true") {
    throw "Kafka container '$containerName' chưa chạy. Hãy chạy: docker compose up -d"
}

foreach ($topic in $topics) {
    Write-Host "Đang tạo topic: $topic"

    docker exec $containerName `
        /opt/kafka/bin/kafka-topics.sh `
        --bootstrap-server $bootstrapServer `
        --create `
        --if-not-exists `
        --topic $topic `
        --partitions 1 `
        --replication-factor 1
}

Write-Host ""
Write-Host "Danh sách Kafka topics:"

docker exec $containerName `
    /opt/kafka/bin/kafka-topics.sh `
    --bootstrap-server $bootstrapServer `
    --list
