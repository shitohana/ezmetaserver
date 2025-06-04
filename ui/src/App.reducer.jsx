import React, { useState, useEffect, useReducer } from "react";
import './scss/App.scss'

import Loader from './parts/Loader';
import Loading from "./parts/Loading";
import SearchIcon from '@mui/icons-material/Search';
import { Alert, Badge, Button, Checkbox, Chip, Divider, IconButton, InputBase, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from "@mui/material";

const MAX_RESULTS = 1000;
const DEFAULT_COLS = ['Study Title', 'Study Abstract'];

const SearchBar = ({ that }) => {
  const [value, setValue] = useState("");
  const [debouncedValue, setDebouncedValue] = useState('');
  const [results, setResults] = useState(false);
  const [valid, setValid] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value.trim());
    }, 1500);
    return () => clearTimeout(timer);
  }, [value]);

  useEffect(() => {
    if (debouncedValue !== '') {
      console.log('Отправка запроса с текстом:', debouncedValue);
      that.loader.get(`dump/peek?term=${encodeURIComponent(debouncedValue)}`, (ret) => {
        setResults(ret.count);
        setValid(ret && ret.count && ret.count > 0 && ret.count < MAX_RESULTS);
      });
    }
  }, [debouncedValue]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!valid) return;

    that.loader.post('dump/fetch', {
      terms: value.split(' '),
      max_results: MAX_RESULTS,
    }, (ret) => {
      if (!ret.metadata) return
      console.log("ret.metadata ->", ret.metadata);
      that.setState({ meta: ret.metadata });
      // let m = expandBy(ret.metadata, 'SAMPLE.SAMPLE_ATTRIBUTES.SAMPLE_ATTRIBUTE');
      // console.log("expanded ->", m);
    });
  };

  return (
    <div className="search-bar-wrapper">
      <div className="search-bar">
        <Paper
          elevation={2}
          component="form"
          className="input-area"
          onSubmit={handleSubmit}
        >
          <div className={`loading-wrapper ${that.state.loaderActive ? 'visible' : ''}`}>
            <Loading />
          </div>
          <InputBase
            value={value}
            onChange={(e) => {
              setValue(e.target.value);
              setValid(false);
              setResults(false);
            }}
            placeholder="Search terms from NCBI databases" />
          <Divider sx={{ height: 28, m: 0.5 }} orientation="vertical" />
          <IconButton disabled={!valid} color={valid ? "primary" : "disabled"} type="submit" aria-label="search">
            <SearchIcon />
          </IconButton>
          <Chip
            className={`results-counter ${results ? 'visible' : ''}`}
            label={results} variant="outlined"
            color={!valid ? 'error' : 'success'} size="small" />
        </Paper>
      </div>
      <Alert className={`s-message error ${!(results > MAX_RESULTS) || 'visible'}`} severity="error">
        There are too many results. Please specify your request.
      </Alert>
    </div>

  );
};

const ColumnsSelector = ({ meta }) => {
  if (!meta || !meta.data || !meta.data.length) return '';

  let chset = {};
  let rows = meta.columns.map((name, index) => {
    let cnt = 0;
    let chips = {};
    chset[name] = DEFAULT_COLS.indexOf(name) !== -1;

    meta.data.map(row => {
      if (row[index]) {
        cnt += 1;
        let words = (row[index] + '').split(' ');
        let txt = words.length > 8 ? (words.slice(0, 10).join(' ') + '...') : row[index];
        txt = String(txt).replace(/<\/?[^>]+(>|$)/g, "");
        if (!chips[txt]) chips[txt] = 0;
        chips[txt] += 1;
      }
    })

    return {
      'id': index,
      'name': name,
      'fill': Math.round(100 * cnt / meta.data.length) + "%",
      'example': Object.entries(chips).sort(([, a], [, b]) => b - a),
    };
  });

  const [checked, setChecked] = useState(chset);
  const [, forceUpdate] = useReducer(x => x + 1, 0);

  const set = (name, to) => {
    console.log('set', name, to)
    checked[name] = to;
    setChecked(checked);
    forceUpdate();
  }
  const setAll = (to) => {
    console.log('setAll', to)
    meta.columns.map(name => checked[name] = to);
    setChecked(checked);
    forceUpdate();
  }
  const total = () => Object.keys(checked).filter(name => checked[name]).length;

  return (
    <div className="col-select">
      <Alert severity="info">
        <strong>Results found: {meta.data.length}.</strong> <br />
        For further processing using AI, select columns for analysis or use default values

        <Button className="ai-start" variant="contained" disableElevation>
          Continue
        </Button>
      </Alert>
      <TableContainer component={Paper} elevation={2}>
        <Table key={total()} size="small">
          <TableHead>
            <TableRow>
              <TableCell>
                <Checkbox
                  onChange={(e) => {
                    if (total() == meta.columns.length) {
                      return setAll(false);
                    }
                    setAll(true);
                  }}
                  checked={total() == meta.columns.length}
                  indeterminate={total() != meta.columns.length && total() > 0}
                  size="small" />
              </TableCell>
              <TableCell>Column Title</TableCell>
              <TableCell>Filled %</TableCell>
              <TableCell>Rows Data sample</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((row) => (
              <TableRow
                key={row.name}
              >
                <TableCell>
                  <Checkbox
                    checked={checked[row.name] === true}
                    onChange={(e) => { set(row.name, !checked[row.name]) }}
                    size="small" />
                </TableCell>
                <TableCell>{row.name}</TableCell>
                <TableCell>{row.fill}</TableCell>
                <TableCell>{row.example.map((v, i) => (
                  <Badge key={i} color="info" badgeContent={v[1]}>
                    <Chip size="small" label={v[0]} variant="outlined" />
                  </Badge>
                ))}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </div>
  );
}

/// !!!!!!!!!!!!
/// !!!!!!!!!!!!

class App extends React.Component {
  constructor(props) {
    super(props);
    this.api = 'http://localhost:9090/api/v1/';
    this.api = 'http://0.0.0.0:9091/proxy?url=http://localhost:9090/api/v1/';
    this.loader = new Loader(this);
    this.state = { terms: '', meta: {} }
    console.log('Example', 'SRP235229')
  }

  render() {
    return (
      <div className="application">
        <SearchBar that={this} />
        <ColumnsSelector meta={this.state.meta} />
      </div>
    )
  }
}

export default App
