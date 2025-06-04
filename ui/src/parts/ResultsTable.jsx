import { useState } from "react";
import {
  Box,
  Button,
  Checkbox,
  FormControlLabel,
  IconButton,
  Paper,
  Tab,
  Toolbar,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import { TabPanel, TabList, TabContext } from "@mui/lab";

import { Download, DownloadTSV } from "./DownloadTsv";

import ResultCard from "../parts/ResultCard";
import WordCloud from "../parts/WordCloud";

const TableMaker = ({ checked, filters, res, columns }) => {
  let table_tsv = [columns];
  let table_ai = [["ID", "TAGS"]];
  let table_download = "";

  res.map((group) => {
    if (checked[group.ID] === false) return;
    if (filters.length) {
      let found = false;
      filters.map((f) => {
        if (group.tagline.indexOf(f) !== -1) found = true;
      });
      if (!found) return;
    }

    table_ai.push([group.ID, group.tagline.join(", ")]);

    group.rows.map((row) => {
      table_tsv.push(columns.map((c) => row[c] || ""));

      if (!row["Download Links"]) return;
      row["Download Links"].map((link) => {
        table_download += "wget " + link + "\n";
      });
    });
  });

  return { table_download, table_ai, table_tsv };
};

export default function ResultsTable({ close, tags, res, columns }) {
  const [filters, setFilters] = useState([]);
  const [checked, setChecked] = useState({});
  const [tab, setTab] = useState("1");

  const swh = (key) => {
    const i = filters.indexOf(key);
    if (i === -1) {
      setFilters((prev) => [...prev, key]);
    } else {
      setFilters((prev) => prev.filter((v) => v != key));
    }
  };

  const tagsort = Object.entries(tags)
    .sort(([, a], [, b]) => b - a)
    .map((tag) => ({
      text: tag[0],
      value: tag[1],
    }));

  return (
    <div className="results-frame">
      <Toolbar>
        <IconButton
          edge="start"
          color="inherit"
          onClick={close}
          aria-label="close"
        >
          <CloseIcon />
        </IconButton>
        <div className="title">Results</div>
        <div className="downloads">
          <Button
            variant="outlined"
            onClick={() => {
              let file = TableMaker({
                checked,
                filters,
                res,
                columns,
              }).table_tsv;
              DownloadTSV(file, "results");
            }}
          >
            results.tsv
          </Button>
          <Button
            variant="outlined"
            onClick={() => {
              let file = TableMaker({
                checked,
                filters,
                res,
                columns,
              }).table_ai;
              DownloadTSV(file, "ai_processed");
            }}
          >
            ai_processed.tsv
          </Button>
          <Button
            variant="outlined"
            onClick={() => {
              let file = TableMaker({
                checked,
                filters,
                res,
                columns,
              }).table_download;
              Download(file, "text/plain", "downloads.txt");
            }}
          >
            downloads.txt
          </Button>
        </div>
      </Toolbar>
      <div className="results-filters">
        <Paper sx={{ width: "100%" }} elevation={2}>
          <TabContext value={tab}>
            <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
              <TabList onChange={(e, v) => setTab(v)}>
                <Tab label="Tags" value="1" />
                <Tab label="World cloud" value="2" />
              </TabList>
            </Box>
            <TabPanel className="taglist" value="1">
              {tagsort.map(({ text, value }) => {
                return (
                  <FormControlLabel
                    key={text}
                    checked={filters.indexOf(text) !== -1}
                    onChange={() => swh(text)}
                    control={<Checkbox size="small" />}
                    label={`${text} (${value})`}
                  />
                );
              })}
            </TabPanel>
            <TabPanel value="2">
              <WordCloud
                w={tagsort}
                filters={filters}
                clc={(txt) => swh(txt)}
              />
            </TabPanel>
          </TabContext>
        </Paper>
      </div>

      <div className="results-table">
        {res.map((one) => (
          <ResultCard
            key={one.ID}
            one={one}
            filters={filters}
            setChecked={setChecked}
          />
        ))}
      </div>
    </div>
  );
}
