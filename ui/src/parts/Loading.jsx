const Loading = (active) => (
  <div className={"loading-dna " + (active ? "active" : "")}>
    <div className={"dna-line"}>
      {[1, 2, 3, 4, 5, 6].map((i) => {
        return (
          <span key={i}>
            <b></b>
          </span>
        );
      })}
    </div>
    <div className={"dna-line reverse"}>
      {[1, 2, 3, 4, 5, 6].map((i) => {
        return (
          <span key={i}>
            <b></b>
          </span>
        );
      })}
    </div>
  </div>
);

export default Loading;
