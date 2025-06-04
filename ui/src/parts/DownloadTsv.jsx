export function Download(text, type, filename = "file") {
  const blob = new Blob([text], { type: type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename; // имя файла
  a.click();
  URL.revokeObjectURL(url);
}

export function DownloadTSV(data, filename = "file") {
  const tsvString = data.map((row) => row.join("\t")).join("\n");
  Download(tsvString, "text/tab-separated-values", filename + ".tsv");
}
