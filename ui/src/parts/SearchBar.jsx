import React, { useState, useEffect } from "react";

import Loading from "./Loading";
import SearchIcon from "@mui/icons-material/Search";
import {
  Alert,
  Chip,
  Divider,
  IconButton,
  InputBase,
  Paper,
} from "@mui/material";

const MAX_RESULTS = 1000;

export default function SearchBar({ loader, set, state }) {
  const [value, setValue] = useState("");
  const [debouncedValue, setDebouncedValue] = useState("");
  const [valid, setValid] = useState(true);
  const [preloaded, setPreloaded] = useState(false);

  useEffect(() => {
    setValid(true);
    set({ meta: false, results: false });
    const timer = setTimeout(() => {
      setDebouncedValue(value.trim());
    }, 1500);
    return () => clearTimeout(timer);
  }, [value]);

  useEffect(() => {
    if (debouncedValue !== "") {
      loader.get(
        `dump/peek?term=${encodeURIComponent(debouncedValue)}`,
        (ret) => {
          set({ results: parseInt(ret.count) });
          setValid(ret && ret.count && ret.count > 0);
        }
      );
    }
  }, [debouncedValue]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!valid) return;
    if (state.loaderActive) return;

    loader.post(
      "dump/fetch",
      {
        terms: [value],
        max_results: MAX_RESULTS,
      },
      (ret) => {
        if (!ret.metadata) return;
        console.log("ret.metadata ->", ret.metadata);
        set({ meta: ret.metadata });
        setPreloaded(true);
      }
    );
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
          <div
            className={`loading-wrapper ${
              state["loading:dump/fetch"] ? "visible" : ""
            }`}
          >
            <Loading />
          </div>
          <InputBase
            value={value}
            onChange={(e) => {
              setValue(e.target.value);
              setValid(false);
              setPreloaded(false);
            }}
            placeholder="Search terms from NCBI databases"
          />
          <Divider sx={{ height: 28, m: 0.5 }} orientation="vertical" />
          <IconButton
            disabled={state.results === 0}
            color="primary"
            type="submit"
            aria-label="search"
          >
            <SearchIcon />
          </IconButton>
          <Chip
            className={`results-counter ${
              state.results !== false ? "visible" : ""
            }`}
            label={state.results}
            variant="outlined"
            color={!valid ? "error" : "success"}
            size="small"
          />
        </Paper>
      </div>
      {!preloaded || state.results === 0 ? (
        <>
          <Alert
            className={`s-message error ${
              state.results === 0 ? "visible" : ""
            }`}
            severity="error"
          >
            Nothing was found for your request.
          </Alert>
          <Alert
            className={`s-message error ${
              !(state.results > MAX_RESULTS) || "visible"
            }`}
            severity="error"
          >
            There are too many results. Please specify your request or only the
            first {MAX_RESULTS} experiments will be included in the results.
          </Alert>
        </>
      ) : (
        ""
      )}
    </div>
  );
}
