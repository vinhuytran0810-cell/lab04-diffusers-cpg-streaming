param(
    [Parameter(Mandatory = $true)]
    [string]$FileId,

    [string]$ExpectedHash = "",

    [long]$ExpectedOffset = -1,

    [string]$ContainerName = "lab04-mongodb",

    [string]$Database = "bigdata_lab04",

    [string]$Collection = "source_metadata"
)

$ErrorActionPreference = "Stop"

$runningContainer = docker ps `
    --filter "name=^/${ContainerName}$" `
    --format "{{.Names}}"

if ($runningContainer -ne $ContainerName) {
    throw "MongoDB container '$ContainerName' chưa chạy. Hãy chạy: docker compose up -d"
}

$mongoScript = @"
const database = db.getSiblingDB("__DATABASE__");
const collection = database.getCollection("__COLLECTION__");
const fileId = "__FILE_ID__";

const document = collection.findOne({ _id: fileId });

const result = {
    count: collection.countDocuments({ _id: fileId }),
    exists: document !== null,
    content_hash: document ? document.content_hash : null,
    kafka_offset: document && document.kafka_offset !== undefined
        ? Number(document.kafka_offset)
        : null,
    node_count: document && document.metadata
        ? Number(document.metadata.node_count)
        : null,
    function_count: document && document.metadata
        ? Number(document.metadata.function_count)
        : null
};

print(JSON.stringify(result));
"@

$mongoScript = $mongoScript.Replace("__DATABASE__", $Database)
$mongoScript = $mongoScript.Replace("__COLLECTION__", $Collection)
$mongoScript = $mongoScript.Replace("__FILE_ID__", $FileId)

$rawOutput = $mongoScript |
    docker exec -i $ContainerName mongosh --quiet

if ($LASTEXITCODE -ne 0) {
    throw "Không thể truy vấn MongoDB."
}

$jsonLine = $rawOutput |
    ForEach-Object {
        if ($_ -match '(\{.*\})') {
            $Matches[1]
        }
    } |
    Select-Object -Last 1

if (-not $jsonLine) {
    Write-Host "Dữ liệu thô nhận được từ mongosh:"
    $rawOutput | ForEach-Object { Write-Host $_ }

    throw "Không tìm thấy kết quả JSON hợp lệ từ MongoDB."
}

$result = $jsonLine | ConvertFrom-Json
$hasFailure = $false

if ($result.exists -and $result.count -eq 1) {
    Write-Host "PASS: Tìm thấy đúng 1 document cho file_id."
}
else {
    Write-Host "FAIL: Số document tìm thấy là $($result.count)."
    $hasFailure = $true
}

if ($ExpectedHash -ne "") {
    if ($result.content_hash -eq $ExpectedHash) {
        Write-Host "PASS: content_hash khớp giá trị mong đợi."
    }
    else {
        Write-Host "FAIL: content_hash không khớp."
        Write-Host "  Expected: $ExpectedHash"
        Write-Host "  Actual:   $($result.content_hash)"
        $hasFailure = $true
    }
}

if ($ExpectedOffset -ge 0) {
    if ([long]$result.kafka_offset -eq $ExpectedOffset) {
        Write-Host "PASS: kafka_offset = $ExpectedOffset."
    }
    else {
        Write-Host "FAIL: kafka_offset không khớp."
        Write-Host "  Expected: $ExpectedOffset"
        Write-Host "  Actual:   $($result.kafka_offset)"
        $hasFailure = $true
    }
}

Write-Host ""
Write-Host "MongoDB document:"
Write-Host "  file_id:        $FileId"
Write-Host "  content_hash:   $($result.content_hash)"
Write-Host "  kafka_offset:   $($result.kafka_offset)"
Write-Host "  node_count:     $($result.node_count)"
Write-Host "  function_count: $($result.function_count)"

if ($hasFailure) {
    exit 1
}

Write-Host ""
Write-Host "MongoDB verification completed successfully."
exit 0
