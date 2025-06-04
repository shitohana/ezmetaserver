import React, { useState } from "react";

import {
  Alert,
  Badge,
  Button,
  Checkbox,
  Chip,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from "@mui/material";

export const DEFAULT_COLS = ["Study Title", "Study Abstract"];
export const PKEY = "Study Accession";

const CompactWord = (txt, limit = 35) => {
  let final = [];
  let chars = 0;

  for (let one of (txt + "").split(" ")) {
    if (!one) continue;
    if (chars + one.length > limit) {
      if (final.length > 0) {
        final.push(one + "...");
      } else {
        final.push(one.substring(0, limit) + "...");
      }
      break;
    } else {
      chars += one.length;
      final.push(one);
    }
  }
  return String(final.join(" ")).replace(/<\/?[^>]+(>|$)/g, "");
};

const MakeResultsAI = (table, columns) => {
  let tags = {};
  const res = Object.keys(table).map((ID) => {
    let tagline = [];
    for (let tp in table[ID].result) {
      table[ID].result[tp].map((tag) => {
        if (tagline.indexOf(tag) === -1) tagline.push(tag);
        if (!tags[tag]) tags[tag] = 0;
        tags[tag] += 1;
      });
    }

    return {
      ID: ID,
      desc: DEFAULT_COLS.map((c) => ({
        col: c,
        text: table[ID].rows[0][columns.indexOf(c)],
      })),
      rows: table[ID].rows.map((row, ri) => {
        let obj = { id: ri };
        columns.map((col, ci) => {
          if (col.indexOf(DEFAULT_COLS) !== -1 || col == PKEY) return;
          obj[col] = row[ci];
        });
        return obj;
      }),
      tagline: tagline,
    };
  });

  return { tags, res, columns };
};

export default function ColumnsSelector({ loader, state, set }) {
  let meta = state.meta;
  if (!meta || !meta.data || !meta.data.length) return "";

  const [checked, setChecked] = useState(DEFAULT_COLS);
  const [sended, setSended] = useState(false);

  let rows = meta.columns.map((name, index) => {
    let cnt = 0;
    let chips = {};
    meta.data.map((row) => {
      if (row[index]) {
        cnt += 1;
        if (!chips[row[index]]) chips[row[index]] = 0;
        chips[row[index]] += 1;
      }
    });
    const pc = Math.round((100 * cnt) / meta.data.length);
    return {
      name: name,
      cls: pc == 100 ? "full" : pc > 30 ? "norm" : "bad",
      fill: pc + "%",
      example: Object.entries(chips).sort(([, a], [, b]) => b - a),
    };
  });

  const AI = () => {
    let index = meta.columns.indexOf(PKEY);
    if (index === -1) {
      return console.log("PK not found!", PKEY, meta);
    }

    let studies = {};
    meta.data.map((row) => {
      if (!studies[row[index]]) {
        studies[row[index]] = { rows: [], txt: {} };
      }
      studies[row[index]].rows.push(row);

      meta.columns.map((col, ci) => {
        if (checked.indexOf(col) === -1) return;
        studies[row[index]].txt[row[ci]] = true;
      });
    });

    // console.log("studies", studies);
    setSended(true);
    loader.post(
      "nlp/process",
      {
        entries: Object.keys(studies).map((sid) => ({
          id: sid,
          text: Object.keys(studies[sid].txt).join("\n"),
        })),
        model_type: "aioner",
      },
      (ret) => {
        console.log("AI ->", ret);
        ret.results.map(({ id, result }) => {
          studies[id].result = result;
        });
        set({ modal: true, ai: MakeResultsAI(studies, meta.columns) });
        setSended(false);
      }
    );
  };

  return (
    <div className="col-select">
      <Alert severity="info">
        <strong>Results found: {meta.data.length}.</strong> <br />
        For further processing using AI, select columns for analysis or use
        default values
        <Button
          onClick={() => AI()}
          disabled={checked.length === 0 || sended}
          className="ai-start"
          variant="contained"
          disableElevation
        >
          {sended ? "..." : "Continue"}
        </Button>
      </Alert>
      <TableContainer component={Paper} elevation={2}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>
                <Checkbox
                  onChange={(e) => {
                    if (checked.length == meta.columns.length)
                      return setChecked([]);
                    setChecked(meta.columns);
                  }}
                  checked={checked.length == meta.columns.length}
                  indeterminate={
                    checked.length != meta.columns.length && checked.length > 0
                  }
                  size="small"
                />
              </TableCell>
              <TableCell>Column Title</TableCell>
              <TableCell>Filled %</TableCell>
              <TableCell>Rows Data sample</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((row) => (
              <TableRow key={row.name}>
                <TableCell>
                  <Checkbox
                    onChange={(e) => {
                      if (checked.indexOf(row.name) !== -1) {
                        setChecked(checked.filter((e) => e != row.name));
                      } else {
                        setChecked(checked.concat([row.name]));
                      }
                    }}
                    checked={checked.indexOf(row.name) !== -1}
                    size="small"
                  />
                </TableCell>
                <TableCell>{row.name}</TableCell>
                <TableCell className="filled">
                  <div className="filled-line">
                    <span className="pc">{row.fill}</span>
                    <span className="l">
                      <span
                        style={{ width: row.fill }}
                        className={`filled-area ${row.cls}`}
                      ></span>
                    </span>
                  </div>
                </TableCell>
                <TableCell>
                  {row.example.map((v, i) => (
                    <Badge key={i} color="info" badgeContent={v[1]}>
                      <Chip
                        size="small"
                        label={CompactWord(v[0])}
                        variant="outlined"
                      />
                    </Badge>
                  ))}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </div>
  );
}
