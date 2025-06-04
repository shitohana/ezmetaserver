import { useState } from "react";
import { Button, Card, Checkbox, Chip, IconButton } from "@mui/material";
import CloudDownloadIcon from "@mui/icons-material/CloudDownload";
import { DataGrid } from "@mui/x-data-grid";

const DEFAULT_VISIBLE_COLS = [
  "Experiment Accession",
  "Experiment Title",
  "Experiment ID",
  "Study Accession",
  "Study Title",
  "Sample Accession",
  "Sample Alias",
  "Taxon ID",
  "Library Name",
  "Run Accession",
  "Download Links",
];

export default function ResultCard({ one, filters, setChecked }) {
  const [expanded, setExpanded] = useState(false);

  if (filters.length > 0) {
    let found = false;
    one.tagline.map((tag) => {
      if (filters.indexOf(tag) !== -1) found = true;
    });
    if (!found) {
      return "";
    }
  }

  const visible = {};

  const cols = Object.keys(one.rows[0])
    .filter((col) => col != "id")
    .map((col) => {
      let c = { field: col, headerName: col };
      if (DEFAULT_VISIBLE_COLS.indexOf(col) === -1) {
        visible[col] = false;
      }
      c.width = col.length * 8 + 10;
      if (col == "Download Links") {
        c.renderCell = (row) => {
          if (!row.formattedValue.length) return "";
          return (
            <IconButton href={row.formattedValue[0]} color="primary">
              <CloudDownloadIcon />
            </IconButton>
          );
        };
      }
      return c;
    });

  return (
    <Card elevation={2}>
      <div className="result">
        <div className="result-head">
          <span className="id">
            <Checkbox
              onChange={() => {
                setChecked((prev) => {
                  if (prev[one.ID] === undefined || prev[one.ID] === true) {
                    prev[one.ID] = false;
                  } else {
                    prev[one.ID] = true;
                  }
                  return prev;
                });
              }}
              defaultChecked
            />
            {one.ID}
          </span>
          <div className="result-tags">
            {one.tagline.map((tag) => (
              <Chip
                key={tag}
                size="small"
                label={tag}
                color={
                  filters.length && filters.indexOf(tag) !== -1 ? "success" : ""
                }
              />
            ))}
          </div>
        </div>
        {one.desc.map((d) => (
          <p key={d.col}>
            <strong>{d.col}:</strong> {d.text}
          </p>
        ))}

        <Button
          variant="outlined"
          size="small"
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? "Hide" : `Expand Experiments (${one.rows.length})`}
        </Button>
      </div>
      {expanded ? (
        <div
          className="expanded"
          style={{ height: one.rows.length > 13 ? "500px" : "auto" }}
        >
          <DataGrid
            rowHeight={30}
            rows={one.rows}
            columns={cols}
            initialState={{
              columns: {
                columnVisibilityModel: visible,
              },
              pagination: {
                paginationModel: {
                  pageSize: 50,
                },
              },
            }}
          />
        </div>
      ) : (
        ""
      )}
    </Card>
  );
}
