import React, { useState } from "react";
import { Dialog } from "@mui/material";

import "./scss/App.scss";

import Loader from "./parts/Loader";
import SearchBar from "./parts/SearchBar";
import ColumnsSelector from "./parts/ColumnsSelector";
import ResultsTable from "./parts/ResultsTable";

class App extends React.Component {
  constructor(props) {
    super(props);
    //this.api = "http://localhost:9090/api/v1/";
    //this.api = "http://0.0.0.0:9091/proxy?url=http://localhost:9090/api/v1/";
    this.api = "/api/v1/";
    this.loader = new Loader(this);
    this.state = { terms: "", meta: {}, results: false, modal: false, ai: {} };
    console.log("> Example:");
    console.log("SRP235229");
    console.log("Symmetric arginine TRANSCRIPTOMIC RNA-Seq");
  }

  render() {
    return (
      <>
        <Dialog
          fullScreen
          open={this.state.modal}
          onClose={() => this.setState({ modal: false })}
        >
          <ResultsTable
            {...this.state.ai}
            close={() => this.setState({ modal: false })}
          />
        </Dialog>
        <div className="application">
          <SearchBar
            set={this.setState.bind(this)}
            loader={this.loader}
            state={this.state}
          />
          <ColumnsSelector
            set={this.setState.bind(this)}
            loader={this.loader}
            state={this.state}
          />
        </div>
      </>
    );
  }
}

export default App;
