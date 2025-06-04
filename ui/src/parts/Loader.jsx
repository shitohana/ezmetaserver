import axios from "axios";

class Loader {
  constructor(parent) {
    this.parent = parent;
    this.api = parent.api === undefined ? `${window.basename}api/` : parent.api;
    this.cancel = {};
  }

  get(path, onResult) {
    return this.request(path, "get", {}, onResult);
  }

  post(path, data, onResult) {
    return this.request(path, "post", data, onResult);
  }

  request(path, method, data, onResult) {
    if (this.cancel[path]) {
      this.cancel[path].cancel("Request canceled by user");
    }

    const CancelToken = axios.CancelToken;
    this.cancel[path] = CancelToken.source();

    const l = `loading:${path}`;
    this.parent.setState({ [l]: true });
    // this.parent.setState({ 'loaderActive': true });

    const obj = {
      url: this.api + path,
      method: method,
      data: data || {},
      cancelToken: this.cancel[path].token,
    };

    axios(obj)
      .then((res) => {
        //this.parent.setState({ ["data:" + path]: res.data });
        this.parent.setState({ [l]: false });
        // this.parent.setState({ 'loaderActive': false });
        if (onResult) onResult(res.data, path);
      })
      .catch((thrown) => {
        if (axios.isCancel(thrown)) {
          console.log("[STOP]", thrown.message);
        } else {
          console.log("[ERROR]", thrown.message);
          this.parent.setState({ loaderActive: false });
          //this.parent.setState({ [l]: false });
        }
      });
  }
}

export default Loader;
