$ErrorActionPreference = "Stop"

$projectPath = (Get-Location).Path
$networkName = "lab04-diffusers-cpg-streaming_default"
$containerName = "lab04-spark-stream"
$sparkImage = "apache/spark:4.2.0-scala2.13-java17-python3-ubuntu"

$existingContainer = docker ps -a `
    --filter "name=^/${containerName}$" `
    --format "{{.Names}}"

if ($existingContainer -eq $containerName) {
    Write-Host "Đang xóa Spark container cũ..."
    docker rm -f $containerName | Out-Null
}

Write-Host "Đang khởi động Spark Structured Streaming..."

docker run --rm -it `
    --name $containerName `
    --network $networkName `
    --user root `
    -v "${projectPath}:/opt/project" `
    -w /opt/project `
    -e KAFKA_BOOTSTRAP_SERVERS=kafka:29092 `
    -e KAFKA_METADATA_TOPIC=diffusers.source.metadata.v1 `
    -e MONGODB_URI=mongodb://mongodb:27017 `
    -e MONGODB_DATABASE=bigdata_lab04 `
    -e MONGODB_COLLECTION=source_metadata `
    -e SPARK_CHECKPOINT_PATH=/opt/project/checkpoints/metadata_stream `
    $sparkImage `
    bash -lc "python3 -m pip install --no-cache-dir python-dotenv && /opt/spark/bin/spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.13:4.2.0,org.mongodb.spark:mongo-spark-connector_2.13:11.1.0 src/streaming/metadata_to_mongodb.py"
